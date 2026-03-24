"""Pydantic schemas for API contracts."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class ExperimentUploadResponse(BaseModel):
    """Response after uploading an evaluation dataset."""

    experiment_id: str


class ExperimentRunRequest(BaseModel):
    """Request to run evaluation for an experiment."""

    experiment_id: str
    rubric: dict[str, Any]
    temperature: Optional[float] = 0.2


class ExperimentDetailResponse(BaseModel):
    """Detailed experiment response with results and metrics."""

    experiment_id: str
    status: str
    metrics: "ExperimentMetricsSchema | dict[str, Any]"
    results: list["EvaluationResultSchema"]


class EvaluationResultSchema(BaseModel):
    """Structured evaluation result payload."""

    item_id: str
    rubric_scores: dict[str, Any]
    overall_score: float
    reasoning: str


class ExperimentMetricsSchema(BaseModel):
    """Aggregate metrics for an experiment."""

    mean_score: float
    safety_fail_rate: float
    std_dev: float


class ExperimentCompareResponse(BaseModel):
    """Comparison response for two experiments."""

    baseline_experiment_id: str
    candidate_experiment_id: str
    regression_detected: bool
    delta_mean_score: float


class CIGateResponse(BaseModel):
    """CI/CD gate decision response."""

    experiment_id: str
    mean_score: float
    regression_detected: bool
    deployment_allowed: bool
