"""LLM client wrapper supporting OpenAI and Ollama."""

from __future__ import annotations

import logging

from openai import OpenAI

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

        client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=settings.llm_timeout_seconds
        )
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                response_format={"type": "json_object"} if settings.llm_provider == "openai" else None,
            )
        except Exception as exc:
            logger.exception(f"{settings.llm_provider.upper()} request failed")
            raise RuntimeError("LLM judge request failed") from exc

        content = response.choices[0].message.content
        if not content:
            logger.error(f"{settings.llm_provider.upper()} response missing content")
            raise RuntimeError("LLM judge returned empty response")

        return content
