import pytest

from app.mistral_client import TranslationError
from app.schemas import TranslationResponse
from app.service import DocumentError, TranslationService


class DummyClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, str | None]] = []

    def translate(self, *, document_text: str, target_language: str, format_hint: str | None) -> str:
        self.calls.append(
            {
                "document_text": document_text,
                "target_language": target_language,
                "format_hint": format_hint,
            }
        )
        return f"{document_text} -> {target_language}"


def make_service() -> tuple[TranslationService, DummyClient]:
    client = DummyClient()
    return TranslationService(client), client


def test_translate_file_calls_client_with_expected_payload():
    service, client = make_service()

    response = service.translate_file(
        file_bytes="Hello".encode(),
        filename="readme.md",
        target_language="French",
    )

    assert isinstance(response, TranslationResponse)
    assert response.translated_text == "Hello -> French"
    assert response.filename == "readme.french.md"
    assert client.calls == [
        {
            "document_text": "Hello",
            "target_language": "French",
            "format_hint": "Markdown",
        }
    ]


def test_empty_document_raises_document_error():
    service, _ = make_service()

    with pytest.raises(DocumentError):
        service.translate_file(file_bytes=b"", filename="test.txt", target_language="Spanish")


def test_unable_to_decode_document():
    service, _ = make_service()

    with pytest.raises(DocumentError):
        service.translate_file(file_bytes=b"\xff\xfe\xfd", filename="foo.txt", target_language="German")


def test_client_error_is_propagated():
    class ErrorClient(DummyClient):
        def translate(self, *, document_text: str, target_language: str, format_hint: str | None) -> str:
            raise TranslationError("boom")

    service = TranslationService(ErrorClient())

    with pytest.raises(TranslationError):
        service.translate_file(file_bytes="content".encode(), filename="foo.txt", target_language="Italian")
