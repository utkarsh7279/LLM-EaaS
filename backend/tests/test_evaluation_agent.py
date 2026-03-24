from dataclasses import dataclass

from app.models.evaluation import EvaluationItem
from app.services.evaluation_agent import EvaluationAgent


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
