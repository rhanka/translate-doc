"""Pydantic schemas used by the translation backend."""
from __future__ import annotations

from pydantic import BaseModel, Field


class TranslationResponse(BaseModel):
    """Response returned after a successful translation request."""

    filename: str = Field(..., description="Name of the translated document")
    translated_text: str = Field(..., description="Document content translated to the requested language")
