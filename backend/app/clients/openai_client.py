"""LLM client wrapper supporting OpenAI and Ollama."""

from __future__ import annotations

import logging

import httpx

from app.core.config import get_settings

class OpenAIClient:
    """Minimal wrapper to isolate LLM provider calls."""

    def generate_judge_response(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        """Send prompts to the LLM and return raw text."""
        settings = get_settings()
        logger = logging.getLogger(__name__)

        # Determine which provider to use
        if settings.llm_provider == "ollama":
            base_url = settings.llm_base_url or "http://localhost:11434/v1"
            api_key = "ollama"  # Ollama doesn't need a real API key
            model = settings.llm_model
        else:  # openai
            base_url = settings.llm_base_url
            api_key = settings.llm_api_key or settings.openai_api_key
            model = settings.llm_model or settings.openai_model

        try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
            }
            if settings.llm_provider == "openai":
                payload["response_format"] = {"type": "json_object"}

            with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
                response = client.post(
                    f"{base_url.rstrip('/')}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                response_data = response.json()
        except httpx.HTTPStatusError as exc:
            logger.exception(f"{settings.llm_provider.upper()} request failed with HTTP error")
            status_code = exc.response.status_code if exc.response is not None else "unknown"
            response_text = exc.response.text if exc.response is not None else ""
            raise RuntimeError(
                f"LLM judge request failed: HTTP {status_code} {response_text}"
            ) from exc
        except Exception as exc:
            logger.exception(f"{settings.llm_provider.upper()} request failed")
            raise RuntimeError(f"LLM judge request failed: {exc}") from exc

        content = (
            response_data.get("choices", [{}])[0]
            .get("message", {})
            .get("content")
        )
        if not content:
            logger.error(f"{settings.llm_provider.upper()} response missing content")
            raise RuntimeError("LLM judge returned empty response")

        return content
