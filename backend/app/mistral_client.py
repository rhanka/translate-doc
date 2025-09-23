"""Client utilities for interacting with the Mistral API."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Optional

import requests

DEFAULT_MODEL = os.getenv("MISTRAL_MODEL", "mistral-large-latest")
DEFAULT_BASE_URL = os.getenv("MISTRAL_API_BASE", "https://api.mistral.ai/v1")


class TranslationError(RuntimeError):
    """Raised when the translation provider returns an error."""


@dataclass
class MistralClient:
    """Minimal client wrapper around the Mistral chat completion endpoint."""

    api_key: Optional[str]
    model: str = DEFAULT_MODEL
    base_url: str = DEFAULT_BASE_URL
    temperature: float = 0.2
    timeout: int = 60
    _session: Optional[requests.Session] = None

    @property
    def session(self) -> requests.Session:
        """Return a requests session, creating one on demand."""

        if self._session is None:
            self._session = requests.Session()
        return self._session

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise TranslationError("MISTRAL_API_KEY environment variable is not configured.")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def translate(self, *, document_text: str, target_language: str, format_hint: Optional[str] = None) -> str:
        """Translate ``document_text`` to ``target_language`` using the chat endpoint."""

        if not document_text.strip():
            raise TranslationError("The uploaded document is empty.")

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a professional translator. Translate the content you receive while "
                    "preserving its original formatting, layout, markup, metadata and code snippets."
                ),
            },
            {
                "role": "user",
                "content": self._build_user_message(document_text=document_text, target_language=target_language, format_hint=format_hint),
            },
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }

        url = f"{self.base_url.rstrip('/')}/chat/completions"

        try:
            response = self.session.post(url, headers=self._headers(), data=json.dumps(payload), timeout=self.timeout)
        except requests.RequestException as exc:  # pragma: no cover - network issue representation
            raise TranslationError(f"Could not reach the Mistral API: {exc}") from exc

        if response.status_code >= 400:
            raise TranslationError(f"Mistral API returned status {response.status_code}: {response.text}")

        try:
            payload = response.json()
        except ValueError as exc:  # pragma: no cover - unexpected API payload
            raise TranslationError("Received an invalid JSON response from Mistral.") from exc

        try:
            return payload["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:  # pragma: no cover - unexpected payload shape
            raise TranslationError("The response from Mistral did not contain a translation.") from exc

    @staticmethod
    def _build_user_message(*, document_text: str, target_language: str, format_hint: Optional[str]) -> str:
        instructions = [
            f"Translate the document into {target_language}.",
            "Keep the structure identical: preserve headings, tables, bullet lists, emphasis, HTML tags and code blocks.",
            "Do not translate code identifiers or file paths. Maintain placeholders such as {{variable}} or <tag> as-is.",
        ]
        if format_hint:
            instructions.append(f"The document format is {format_hint}.")

        instructions_text = "\n".join(instructions)
        return f"{instructions_text}\n\n---DOCUMENT START---\n{document_text}\n---DOCUMENT END---"
