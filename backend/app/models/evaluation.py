"""Domain models for evaluation workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


RubricConfig = dict[str, Any]


@dataclass(frozen=True)
class EvaluationItem:
    """Input row to be evaluated by the LLM judge."""

    prompt: str
    model_output: str
    reference_output: Optional[str] = None


@dataclass(frozen=True)
class EvaluationResult:
    """Normalized evaluation output for a single item."""

    rubric_scores: dict[str, Any]
    overall_score: float
    reasoning: str
