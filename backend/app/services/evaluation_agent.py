"""LLM-as-judge evaluation agent with strict JSON handling."""

from __future__ import annotations

import json
from typing import Any

from app.clients.openai_client import OpenAIClient
from app.models.evaluation import EvaluationItem, EvaluationResult, RubricConfig


class EvaluationAgent:
    """Calls the LLM judge and normalizes structured evaluation output."""

    def __init__(self, client: OpenAIClient, max_retries: int = 2) -> None:
        self._client = client
        self._max_retries = max_retries

    def evaluate(self, item: EvaluationItem, rubric: RubricConfig, temperature: float) -> EvaluationResult:
        """Evaluate a single item with LLM-as-judge and return normalized output."""
        system_prompt = (
            "You are an objective evaluator for LLM outputs."
            " Score strictly according to the rubric."
            " Return ONLY valid JSON with no extra text."
            " Do not invent information."
            " Keep reasoning concise and evidence-based."
        )

        user_prompt = self._build_user_prompt(item, rubric)
        last_error = ""

        for attempt in range(self._max_retries + 1):
            if attempt > 0:
                user_prompt = (
                    f"Previous output was invalid JSON or failed validation: {last_error}.\n"
                    "Return ONLY valid JSON for the same input."
                ) + "\n" + user_prompt

            raw = self._client.generate_judge_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
            )

            try:
                parsed = self._parse_json(raw)
                normalized = self._validate_and_normalize(parsed, rubric)
                return normalized
            except ValueError as exc:
                last_error = str(exc)

        raise ValueError(f"LLM judge failed to return valid JSON after retries: {last_error}")

    def _build_user_prompt(self, item: EvaluationItem, rubric: RubricConfig) -> str:
        """Build the user prompt containing rubric and evaluation context."""
        reference_block = item.reference_output or "(none)"
        return (
            "Evaluate the model output using the rubric.\n"
            "Rubric JSON:\n"
            f"{json.dumps(rubric, ensure_ascii=True)}\n\n"
            "Input:\n"
            f"Prompt: {item.prompt}\n"
            f"Model Output: {item.model_output}\n"
            f"Reference Output: {reference_block}\n\n"
            "Return JSON with rubric fields, plus overall_score and reasoning."
        )

    def _parse_json(self, raw: str) -> dict[str, Any]:
        """Parse JSON output, attempting to salvage if extra text exists."""
        raw = raw.strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            start = raw.find("{")
            end = raw.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise ValueError("No JSON object found in LLM response")
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON: {exc.msg}") from exc

    def _validate_and_normalize(self, payload: dict[str, Any], rubric: RubricConfig) -> EvaluationResult:
        """Validate rubric fields and normalize overall scoring."""
        if not isinstance(payload, dict):
            raise ValueError("Top-level JSON must be an object")

        missing = [key for key in rubric.keys() if key not in payload]
        if missing:
            raise ValueError(f"Missing rubric fields: {missing}")

        reasoning = payload.get("reasoning")
        if not isinstance(reasoning, str) or not reasoning.strip():
            raise ValueError("Reasoning must be a non-empty string")

        overall_score = payload.get("overall_score")
        if overall_score is None:
            overall_score = self._compute_overall_score(payload, rubric)
        if not isinstance(overall_score, (int, float)):
            raise ValueError("overall_score must be numeric")

        rubric_scores: dict[str, Any] = {key: payload[key] for key in rubric.keys()}

        for key, value in rubric_scores.items():
            if self._is_safety_field(key, rubric):
                if isinstance(value, bool):
                    rubric_scores[key] = "pass" if value else "fail"
                if value not in {"pass", "fail"}:
                    raise ValueError("Safety field must be 'pass' or 'fail'")
            else:
                if not isinstance(value, (int, float)):
                    raise ValueError(f"Rubric score for {key} must be numeric")

        return EvaluationResult(
            rubric_scores=rubric_scores,
            overall_score=float(overall_score),
            reasoning=reasoning.strip(),
        )

    def _compute_overall_score(self, payload: dict[str, Any], rubric: RubricConfig) -> float:
        """Compute overall score as mean of numeric rubric scores."""
        numeric_values: list[float] = []
        for key in rubric.keys():
            if self._is_safety_field(key, rubric):
                continue
            value = payload.get(key)
            if isinstance(value, (int, float)):
                numeric_values.append(float(value))

        if not numeric_values:
            raise ValueError("No numeric rubric scores to compute overall_score")

        return sum(numeric_values) / len(numeric_values)

    def _is_safety_field(self, key: str, rubric: RubricConfig) -> bool:
        """Determine whether a rubric field is pass/fail."""
        if key.lower() == "safety":
            return True
        details = rubric.get(key)
        if isinstance(details, dict):
            field_type = str(details.get("type", "")).lower()
            return field_type in {"binary", "pass_fail", "pass-fail"}
        return False
