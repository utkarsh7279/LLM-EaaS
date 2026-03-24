"""HTTP routes for experiment lifecycle actions."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.openai_client import OpenAIClient
from app.core.config import get_settings
from app.db.session import get_session
from app.models.schemas import (
    CIGateResponse,
    ExperimentCompareResponse,
    ExperimentDetailResponse,
    ExperimentRunRequest,
    ExperimentUploadResponse,
)
from app.services.evaluation_agent import EvaluationAgent
from app.services.evaluation_service import EvaluationService
from app.services.experiment_service import ExperimentService

router = APIRouter()
logger = logging.getLogger(__name__)


def get_experiment_service(session: AsyncSession = Depends(get_session)) -> ExperimentService:
    """Provide ExperimentService with dependencies."""
    settings = get_settings()
    agent = EvaluationAgent(client=OpenAIClient(), max_retries=settings.max_judge_retries)
    evaluation_service = EvaluationService(agent=agent)
    return ExperimentService(session=session, evaluation_service=evaluation_service, settings=settings)


@router.post("/upload", response_model=ExperimentUploadResponse)
async def upload_experiment(
    file: UploadFile = File(...),
    service: ExperimentService = Depends(get_experiment_service),
) -> ExperimentUploadResponse:
    """Upload CSV dataset and create a new experiment."""
    try:
        file_content = await file.read()
        return await service.upload_experiment(file_content=file_content, filename=file.filename or "dataset.csv")
    except ValueError as exc:
        logger.warning("Upload failed: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/run", response_model=ExperimentDetailResponse)
async def run_experiment(
    payload: ExperimentRunRequest,
    service: ExperimentService = Depends(get_experiment_service),
) -> ExperimentDetailResponse:
    """Run evaluation for an experiment."""
    try:
        return await service.run_experiment(payload)
    except ValueError as exc:
        logger.warning("Run failed: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{experiment_id}", response_model=ExperimentDetailResponse)
async def get_experiment(
    experiment_id: str,
    service: ExperimentService = Depends(get_experiment_service),
) -> ExperimentDetailResponse:
    """Fetch experiment details and aggregated metrics."""
    try:
        return await service.get_experiment(experiment_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/compare", response_model=ExperimentCompareResponse)
async def compare_experiments(
    baseline: str,
    candidate: str,
    service: ExperimentService = Depends(get_experiment_service),
) -> ExperimentCompareResponse:
    """Compare two experiments and return regression analysis."""
    try:
        return await service.compare_experiments(baseline, candidate)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{experiment_id}/ci-gate", response_model=CIGateResponse)
async def ci_gate(
    experiment_id: str,
    service: ExperimentService = Depends(get_experiment_service),
) -> CIGateResponse:
    """CI/CD gate endpoint for deployment decisions."""
    try:
        return await service.ci_gate(experiment_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
