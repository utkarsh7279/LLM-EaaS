from dataclasses import dataclass
import asyncio

from app.models.evaluation import EvaluationItem
from app.services.evaluation_agent import EvaluationAgent
from app.services.evaluation_service import EvaluationService


@dataclass
class StubClient:
    response: str

    def generate_judge_response(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        _ = (system_prompt, user_prompt, temperature)
        return self.response


def test_evaluation_agent_parses_json() -> None:
    client = StubClient(
        response='{"factuality": 4, "relevance": 5, "clarity": 4, "safety": "pass", "reasoning": "Ok"}'
    )
    agent = EvaluationAgent(client=client)
    result = agent.evaluate(
        item=EvaluationItem(prompt="p", model_output="o", reference_output=None),
        rubric={"factuality": {}, "relevance": {}, "clarity": {}, "safety": {"type": "pass_fail"}},
        temperature=0.2,
    )
    assert result.overall_score == 4.333333333333333


def test_evaluation_agent_salvages_json() -> None:
    client = StubClient(response="prefix {\"factuality\": 5, \"relevance\": 5, \"clarity\": 5, \"safety\": \"pass\", \"overall_score\": 5, \"reasoning\": \"Good\"} suffix")
    agent = EvaluationAgent(client=client)
    result = agent.evaluate(
        item=EvaluationItem(prompt="p", model_output="o", reference_output=None),
        rubric={"factuality": {}, "relevance": {}, "clarity": {}, "safety": {"type": "pass_fail"}},
        temperature=0.2,
    )
    assert result.overall_score == 5


@dataclass
class FailingClient:
    def generate_judge_response(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        _ = (system_prompt, user_prompt, temperature)
        raise RuntimeError("LLM judge request failed with HTTP 401")


def test_evaluation_service_falls_back_on_runtime_error() -> None:
    service = EvaluationService(agent=EvaluationAgent(client=FailingClient()))
    results = asyncio.run(
        service.evaluate_batch(
            items=[EvaluationItem(prompt="p", model_output="safe response", reference_output="safe response")],
            rubric={"factuality": {"min": 0, "max": 5}, "safety": {"type": "pass_fail"}},
            temperature=0.2,
        )
    )
    assert len(results) == 1
    assert results[0].rubric_scores["safety"] in {"pass", "fail"}
    assert isinstance(results[0].overall_score, float)
    assert "fallback" in results[0].reasoning.lower()
