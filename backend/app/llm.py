from __future__ import annotations

import os
from typing import Any

import httpx

from .config import get_settings


class LLMClientError(RuntimeError):
    """Raised when the LLM client encounters an error."""


class MistralClient:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        settings = get_settings()
        self._api_key = api_key or settings.mistral_api_key
        self._model = model or settings.mistral_model
        self._endpoint = os.environ.get("MISTRAL_API_URL", "https://api.mistral.ai/v1/chat/completions")
        if not self._api_key:
            raise LLMClientError("MISTRAL_API_KEY is not configured")

    async def translate(self, *, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": self._model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(self._endpoint, headers=headers, json=payload)
        if response.status_code >= 300:
            raise LLMClientError(
                f"Mistral API error {response.status_code}: {response.text}"
            )
        data = response.json()
        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:  # pragma: no cover - defensive
            raise LLMClientError(f"Unexpected Mistral response: {data}") from exc


class EchoClient:
    """Fallback client used when running without credentials (for tests/dev)."""

    async def translate(self, *, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:  # noqa: D401
        return user_prompt


def get_llm_client() -> MistralClient | EchoClient:
    settings = get_settings()
    if settings.mistral_api_key:
        return MistralClient(settings.mistral_api_key, settings.mistral_model)
    return EchoClient()
