"""Domain services for translating uploaded documents."""
from __future__ import annotations

from pathlib import Path

from .mistral_client import MistralClient
from .schemas import TranslationResponse


class DocumentError(ValueError):
    """Raised when the uploaded document cannot be processed."""


class TranslationService:
    """Coordinates the end-to-end translation workflow."""

    SUPPORTED_EXTENSIONS = {
        ".txt": "plain text",
        ".md": "Markdown",
        ".markdown": "Markdown",
        ".rst": "reStructuredText",
        ".html": "HTML",
        ".htm": "HTML",
        ".json": "JSON",
        ".yml": "YAML",
        ".yaml": "YAML",
    }

    def __init__(self, client: MistralClient) -> None:
        self._client = client

    def translate_file(self, *, file_bytes: bytes, filename: str, target_language: str) -> TranslationResponse:
        """Translate an uploaded document and return a :class:`TranslationResponse`."""

        decoded = self._decode_bytes(file_bytes)
        format_hint = self._detect_format(filename)
        translated_text = self._client.translate(
            document_text=decoded,
            target_language=target_language,
            format_hint=format_hint,
        )
        return TranslationResponse(
            filename=self._output_filename(filename, target_language),
            translated_text=translated_text,
        )

    @staticmethod
    def _decode_bytes(file_bytes: bytes) -> str:
        if not file_bytes:
            raise DocumentError("The uploaded document is empty.")
        for encoding in ("utf-8", "utf-16"):
            try:
                return file_bytes.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise DocumentError("Unable to decode the document. Only UTF-8 and UTF-16 encodings are supported.")

    @classmethod
    def _detect_format(cls, filename: str) -> str | None:
        suffix = Path(filename or "").suffix.lower()
        return cls.SUPPORTED_EXTENSIONS.get(suffix)

    @staticmethod
    def _output_filename(filename: str, target_language: str) -> str:
        path = Path(filename or "document.txt")
        suffix = path.suffix or ".txt"
        stem = path.stem or "document"
        normalised_language = target_language.lower().replace(" ", "-")
        return f"{stem}.{normalised_language}{suffix}"
