import io

from fastapi.testclient import TestClient

from app.main import app, get_service
from app.mistral_client import TranslationError
from app.schemas import TranslationResponse
from app.service import DocumentError, TranslationService


class DummyService(TranslationService):
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def translate_file(self, *, file_bytes: bytes, filename: str, target_language: str) -> TranslationResponse:
        self.calls.append(
            {
                "file_bytes": file_bytes,
                "filename": filename,
                "target_language": target_language,
            }
        )
        return TranslationResponse(filename=f"{filename}.translated", translated_text="translated content")


def test_translate_endpoint_success(monkeypatch):
    service = DummyService()

    app.dependency_overrides[get_service] = lambda: service
    client = TestClient(app)

    response = client.post(
        "/translate",
        files={"file": ("example.md", io.BytesIO(b"hello world"), "text/markdown")},
        data={"target_language": "French"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["filename"] == "example.md.translated"
    assert payload["translated_text"] == "translated content"
    assert service.calls

    app.dependency_overrides.clear()


def test_translate_endpoint_document_error(monkeypatch):
    class ErrorService(TranslationService):
        def translate_file(self, *, file_bytes: bytes, filename: str, target_language: str) -> TranslationResponse:
            raise DocumentError("bad doc")

    app.dependency_overrides[get_service] = lambda: ErrorService(None)  # type: ignore[arg-type]
    client = TestClient(app)

    response = client.post(
        "/translate",
        files={"file": ("example.md", io.BytesIO(b""), "text/markdown")},
        data={"target_language": "French"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "bad doc"
    app.dependency_overrides.clear()


def test_translate_endpoint_translation_error(monkeypatch):
    class ErrorService(TranslationService):
        def translate_file(self, *, file_bytes: bytes, filename: str, target_language: str) -> TranslationResponse:
            raise TranslationError("provider error")

    app.dependency_overrides[get_service] = lambda: ErrorService(None)  # type: ignore[arg-type]
    client = TestClient(app)

    response = client.post(
        "/translate",
        files={"file": ("example.md", io.BytesIO(b"content"), "text/markdown")},
        data={"target_language": "French"},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "provider error"
    app.dependency_overrides.clear()
