"""Service layer for LLM evaluation logic."""

from __future__ import annotations

import logging

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
            result = await run_in_threadpool(self._agent.evaluate, item, rubric, temperature)
            results.append(result)
        return results
