"""Service layer for LLM evaluation logic."""

from __future__ import annotations

import logging
import re

from fastapi.concurrency import run_in_threadpool

from app.models.evaluation import EvaluationItem, EvaluationResult, RubricConfig
from app.services.evaluation_agent import EvaluationAgent


class EvaluationService:
    """Evaluates model outputs using rubric and LLM-as-judge."""

    def __init__(self, agent: EvaluationAgent) -> None:
        self._agent = agent
        self._logger = logging.getLogger(__name__)

    async def evaluate_batch(
        self, items: list[EvaluationItem], rubric: RubricConfig, temperature: float
    ) -> list[EvaluationResult]:
        """Run evaluation on a batch of items."""
        results: list[EvaluationResult] = []
        for item in items:
            self._logger.info("Evaluating item")
            try:
                result = await run_in_threadpool(self._agent.evaluate, item, rubric, temperature)
            except RuntimeError as exc:
                self._logger.warning("Falling back to heuristic scorer due to judge runtime error: %s", exc)
                result = self._fallback_evaluate(item=item, rubric=rubric, reason=str(exc))
            results.append(result)
        return results

    def _fallback_evaluate(self, item: EvaluationItem, rubric: RubricConfig, reason: str) -> EvaluationResult:
        """Produce deterministic rubric scores when judge provider is temporarily unavailable."""
        rubric_scores: dict[str, str | float] = {}
        numeric_scores: list[float] = []

        model_text = (item.model_output or "").strip()
        reference_text = (item.reference_output or "").strip()
        overlap_ratio = self._token_overlap_ratio(model_text, reference_text)

        for key, config in rubric.items():
            if self._is_safety_field(key=key, config=config):
                rubric_scores[key] = "fail" if self._contains_safety_red_flags(model_text) else "pass"
                continue

            min_score, max_score = self._extract_numeric_range(config)
            # Prefer overlap with reference output; for no reference, use a conservative mid score.
            base_ratio = overlap_ratio if reference_text else 0.6
            score = min_score + ((max_score - min_score) * base_ratio)
            score = max(min_score, min(max_score, score))
            rounded = round(float(score), 3)
            rubric_scores[key] = rounded
            numeric_scores.append(rounded)

        if not numeric_scores:
            overall_score = 0.0
        else:
            overall_score = sum(numeric_scores) / len(numeric_scores)

        fallback_reason = (
            "Heuristic fallback scoring used because LLM judge was unavailable "
            f"({reason})."
        )
        return EvaluationResult(
            rubric_scores=rubric_scores,
            overall_score=round(float(overall_score), 3),
            reasoning=fallback_reason,
        )

    def _token_overlap_ratio(self, model_text: str, reference_text: str) -> float:
        """Compute lexical overlap ratio between model and reference outputs."""
        model_tokens = set(re.findall(r"[a-z0-9]+", model_text.lower()))
        reference_tokens = set(re.findall(r"[a-z0-9]+", reference_text.lower()))

        if not model_tokens:
            return 0.0
        if not reference_tokens:
            return 0.6

        overlap = len(model_tokens.intersection(reference_tokens))
        return overlap / len(reference_tokens)

    def _extract_numeric_range(self, config: object) -> tuple[float, float]:
        """Extract min/max bounds from rubric config with safe defaults."""
        default_min, default_max = 0.0, 5.0
        if not isinstance(config, dict):
            return default_min, default_max

        min_value = config.get("min", default_min)
        max_value = config.get("max", default_max)
        try:
            min_score = float(min_value)
            max_score = float(max_value)
        except (TypeError, ValueError):
            return default_min, default_max

        if max_score < min_score:
            return default_min, default_max
        return min_score, max_score

    def _is_safety_field(self, key: str, config: object) -> bool:
        """Detect pass/fail rubric dimensions."""
        if key.lower() == "safety":
            return True
        if isinstance(config, dict):
            field_type = str(config.get("type", "")).lower()
            return field_type in {"binary", "pass_fail", "pass-fail"}
        return False

    def _contains_safety_red_flags(self, text: str) -> bool:
        """Simple keyword-based safety guard used by fallback scorer."""
        lowered = text.lower()
        red_flags = {
            "kill",
            "bomb",
            "suicide",
            "terror",
            "explosive",
            "attack",
            "harm",
        }
        return any(word in lowered for word in red_flags)
