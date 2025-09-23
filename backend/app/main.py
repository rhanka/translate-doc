"""FastAPI application exposing the translation service."""
from __future__ import annotations

import os
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .mistral_client import DEFAULT_BASE_URL, DEFAULT_MODEL, MistralClient, TranslationError
from .schemas import TranslationResponse
from .service import DocumentError, TranslationService


def create_translation_service() -> TranslationService:
    """Instantiate a :class:`TranslationService` configured from environment variables."""

    api_key = os.getenv("MISTRAL_API_KEY")
    model = os.getenv("MISTRAL_MODEL", DEFAULT_MODEL)
    base_url = os.getenv("MISTRAL_API_BASE", DEFAULT_BASE_URL)
    client = MistralClient(api_key=api_key, model=model, base_url=base_url)
    return TranslationService(client)


app = FastAPI(title="Translate Doc API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    app.state.translation_service = create_translation_service()


def get_service() -> TranslationService:
    return app.state.translation_service  # type: ignore[attr-defined]


TargetLanguage = Annotated[str, Form(description="Language in which to translate the document")]


@app.post("/translate", response_model=TranslationResponse)
async def translate_document(
    file: UploadFile = File(..., description="Document to translate"),
    target_language: TargetLanguage = "English",
    service: TranslationService = Depends(get_service),
) -> TranslationResponse:
    file_bytes = await file.read()
    try:
        return service.translate_file(
            file_bytes=file_bytes,
            filename=file.filename or "document.txt",
            target_language=target_language,
        )
    except DocumentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except TranslationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    """Return a simple health payload for observability checks."""

    return {"status": "ok"}
