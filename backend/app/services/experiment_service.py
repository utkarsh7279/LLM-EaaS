"""Service layer for experiment orchestration."""

from __future__ import annotations

import csv
import io
import logging
import math
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.db_models import EvaluationItem, EvaluationResult, Experiment, ExperimentMetrics
from app.models.evaluation import EvaluationItem as EvaluationItemDTO, EvaluationResult as EvaluationResultDTO
from app.models.schemas import (
    CIGateResponse,
    ExperimentCompareResponse,
    ExperimentDetailResponse,
    ExperimentRunRequest,
    ExperimentUploadResponse,
)
from app.services.evaluation_service import EvaluationService
from app.utils.metrics import detect_regression


class ExperimentService:
    """Orchestrates experiment workflows across DB and evaluation layers."""

    def __init__(self, session: AsyncSession, evaluation_service: EvaluationService, settings: Settings) -> None:
        self._session = session
        self._evaluation_service = evaluation_service
        self._settings = settings
        self._logger = logging.getLogger(__name__)

    async def upload_experiment(self, file_content: bytes, filename: str) -> ExperimentUploadResponse:
        """Create experiment and store uploaded dataset rows."""
        rows = self._parse_csv(file_content=file_content, filename=filename)
        self._logger.info("Uploading %s rows", len(rows))

        experiment = Experiment(id=uuid4(), status="uploaded")
        if not self._settings.baseline_experiment_id and not await self._baseline_exists():
            experiment.is_baseline = True
        self._session.add(experiment)

        items = [
            EvaluationItem(
                id=uuid4(),
                experiment_id=experiment.id,
                prompt=row["prompt"],
                model_output=row["model_output"],
                reference_output=row.get("reference_output"),
            )
            for row in rows
        ]
        self._session.add_all(items)
        await self._session.commit()

        return ExperimentUploadResponse(experiment_id=str(experiment.id))

    async def run_experiment(self, payload: ExperimentRunRequest) -> ExperimentDetailResponse:
        """Execute rubric-based evaluation for all items in an experiment."""
        experiment_id = UUID(payload.experiment_id)
        experiment = await self._session.get(Experiment, experiment_id)
        if not experiment:
            raise ValueError("Experiment not found")

        experiment.status = "running"
        await self._session.commit()

        try:
            items = await self._get_items(experiment_id)
            if not items:
                raise ValueError("No items found for experiment")

            evaluation_items = [
                EvaluationItemDTO(
                    prompt=item.prompt,
                    model_output=item.model_output,
                    reference_output=item.reference_output,
                )
                for item in items
            ]

            temperature = payload.temperature or self._settings.judge_temperature_default
            results = await self._evaluation_service.evaluate_batch(
                items=evaluation_items,
                rubric=payload.rubric,
                temperature=temperature,
            )

            await self._clear_existing_results(experiment_id)

            db_results = []
            for item, result in zip(items, results, strict=False):
                db_results.append(
                    EvaluationResult(
                        id=uuid4(),
                        experiment_id=experiment_id,
                        item_id=item.id,
                        rubric_scores=result.rubric_scores,
                        overall_score=result.overall_score,
                        reasoning=result.reasoning,
                    )
                )

            self._session.add_all(db_results)
            metrics = self._compute_metrics(results)
            self._logger.info("Computed metrics: %s", metrics)
            await self._upsert_metrics(experiment_id, metrics)

            experiment.status = "completed"
            await self._session.commit()

            return await self.get_experiment(payload.experiment_id)
        except Exception:
            experiment.status = "failed"
            await self._session.commit()
            raise

    async def get_experiment(self, experiment_id: str) -> ExperimentDetailResponse:
        """Retrieve experiment with per-row results and metrics."""
        experiment_uuid = UUID(experiment_id)
        experiment = await self._session.get(Experiment, experiment_uuid)
        if not experiment:
            raise ValueError("Experiment not found")

        metrics = await self._get_metrics(experiment_uuid)
        results = await self._get_results(experiment_uuid)

        metrics_payload = metrics or {}

        return ExperimentDetailResponse(
            experiment_id=str(experiment.id),
            status=experiment.status,
            metrics=metrics_payload,
            results=results,
        )

    async def compare_experiments(self, baseline: str, candidate: str) -> ExperimentCompareResponse:
        """Compare experiments and compute regression signal."""
        baseline_mean = await self._get_mean_score(experiment_id=baseline)
        candidate_mean = await self._get_mean_score(experiment_id=candidate)

        result = detect_regression(
            baseline_mean=baseline_mean,
            candidate_mean=candidate_mean,
            threshold=self._settings.regression_threshold,
        )

        return ExperimentCompareResponse(
            baseline_experiment_id=baseline,
            candidate_experiment_id=candidate,
            regression_detected=result.regression_detected,
            delta_mean_score=result.delta_mean_score,
        )

    async def _get_mean_score(self, experiment_id: str) -> float:
        """Load the mean score for an experiment from storage."""
        experiment_uuid = UUID(experiment_id)
        metrics = await self._get_metrics(experiment_uuid)
        if not metrics:
            raise ValueError("Metrics not found for experiment")
        return float(metrics["mean_score"])

    async def ci_gate(self, experiment_id: str) -> CIGateResponse:
        """Return CI/CD deployment decision for an experiment."""
        mean_score = await self._get_mean_score(experiment_id=experiment_id)
        baseline_id = await self._get_baseline_experiment_id()

        regression_result = detect_regression(
            baseline_mean=await self._get_mean_score(experiment_id=baseline_id),
            candidate_mean=mean_score,
            threshold=self._settings.regression_threshold,
        )

        deployment_allowed = not regression_result.regression_detected

        return CIGateResponse(
            experiment_id=experiment_id,
            mean_score=mean_score,
            regression_detected=regression_result.regression_detected,
            deployment_allowed=deployment_allowed,
        )

    async def _get_baseline_experiment_id(self) -> str:
        """Resolve the current baseline experiment id for regression checks."""
        if self._settings.baseline_experiment_id:
            return self._settings.baseline_experiment_id

        statement = select(Experiment).where(Experiment.is_baseline.is_(True)).order_by(Experiment.created_at.desc())
        result = await self._session.execute(statement)
        experiment = result.scalars().first()
        if not experiment:
            raise ValueError("Baseline experiment not configured")
        return str(experiment.id)

    def _parse_csv(self, file_content: bytes, filename: str) -> list[dict[str, str]]:
        """Parse uploaded CSV and return row dictionaries."""
        if not filename.lower().endswith(".csv"):
            raise ValueError("Only .csv files are supported")

        text_stream = io.StringIO(file_content.decode("utf-8-sig"))
        reader = csv.DictReader(text_stream)
        if not reader.fieldnames:
            raise ValueError("CSV file must include headers")

        required = {"prompt", "model_output"}
        missing = required - set(reader.fieldnames)
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

        rows: list[dict[str, str]] = []
        for row in reader:
            prompt = (row.get("prompt") or "").strip()
            model_output = (row.get("model_output") or "").strip()
            if not prompt or not model_output:
                continue
            rows.append({
                "prompt": prompt,
                "model_output": model_output,
                "reference_output": (row.get("reference_output") or "").strip() or None,
            })

        if not rows:
            raise ValueError("CSV file contains no rows")

        return rows

    async def _get_items(self, experiment_id: UUID) -> list[EvaluationItem]:
        statement = select(EvaluationItem).where(EvaluationItem.experiment_id == experiment_id)
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def _baseline_exists(self) -> bool:
        statement = select(Experiment.id).where(Experiment.is_baseline.is_(True))
        result = await self._session.execute(statement)
        return result.first() is not None

    async def _clear_existing_results(self, experiment_id: UUID) -> None:
        await self._session.execute(delete(EvaluationResult).where(EvaluationResult.experiment_id == experiment_id))
        await self._session.execute(delete(ExperimentMetrics).where(ExperimentMetrics.experiment_id == experiment_id))
        await self._session.commit()

    async def _get_results(self, experiment_id: UUID) -> list[dict[str, Any]]:
        statement = select(EvaluationResult).where(EvaluationResult.experiment_id == experiment_id)
        result = await self._session.execute(statement)
        rows = result.scalars().all()
        return [
            {
                "item_id": str(row.item_id),
                "rubric_scores": row.rubric_scores,
                "overall_score": row.overall_score,
                "reasoning": row.reasoning,
            }
            for row in rows
        ]

    async def _get_metrics(self, experiment_id: UUID) -> dict[str, float] | None:
        statement = select(ExperimentMetrics).where(ExperimentMetrics.experiment_id == experiment_id)
        result = await self._session.execute(statement)
        metrics = result.scalars().first()
        if not metrics:
            return None
        return {
            "mean_score": metrics.mean_score,
            "safety_fail_rate": metrics.safety_fail_rate,
            "std_dev": metrics.std_dev,
        }

    async def _upsert_metrics(self, experiment_id: UUID, metrics: dict[str, float]) -> None:
        statement = select(ExperimentMetrics).where(ExperimentMetrics.experiment_id == experiment_id)
        result = await self._session.execute(statement)
        existing = result.scalars().first()
        if existing:
            existing.mean_score = metrics["mean_score"]
            existing.safety_fail_rate = metrics["safety_fail_rate"]
            existing.std_dev = metrics["std_dev"]
        else:
            self._session.add(
                ExperimentMetrics(
                    id=uuid4(),
                    experiment_id=experiment_id,
                    mean_score=metrics["mean_score"],
                    safety_fail_rate=metrics["safety_fail_rate"],
                    std_dev=metrics["std_dev"],
                )
            )

    def _compute_metrics(self, results: list[EvaluationResultDTO]) -> dict[str, float]:
        scores = [result.overall_score for result in results]
        if not scores:
            raise ValueError("No scores to compute metrics")

        mean_score = sum(scores) / len(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        std_dev = math.sqrt(variance)

        safety_failures = 0
        for result in results:
            safety = result.rubric_scores.get("safety")
            if safety in {"fail", False, 0}:
                safety_failures += 1

        safety_fail_rate = safety_failures / len(scores)

        return {
            "mean_score": float(mean_score),
            "safety_fail_rate": float(safety_fail_rate),
            "std_dev": float(std_dev),
        }
