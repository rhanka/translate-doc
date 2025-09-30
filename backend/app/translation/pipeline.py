from __future__ import annotations

from pathlib import Path
from typing import Callable

from ..storage import storage
from .docx import translate_docx_file
from .pptx import translate_pptx_file
from .text import translate_text_file

SUPPORTED_EXTENSIONS = {".txt", ".md", ".docx", ".pptx"}


class UnsupportedFileTypeError(ValueError):
    pass


def _scaled_callback(base: float, span: float, callback: Callable[[float, str], None] | None):
    if not callback:
        return None

    def reporter(fraction: float, message: str) -> None:
        callback(base + span * fraction, message)

    return reporter


async def translate_job(
    job_id: str,
    filename: str,
    llm_client,
    progress_callback: Callable[[float, str], None] | None = None,
) -> Path:
    input_path = storage.input_path(job_id, filename)
    output_path = storage.output_path(job_id, filename, suffix="_translated")
    ext = input_path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileTypeError(f"Unsupported file type: {ext}")

    if ext in {".txt", ".md"}:
        if progress_callback:
            progress_callback(0.05, "Translating text document")
        await translate_text_file(input_path, output_path, llm_client)
        if progress_callback:
            progress_callback(1.0, "Translation completed")
        return output_path

    if ext == ".docx":
        if progress_callback:
            progress_callback(0.05, "Analyzing DOCX structure")
        callback = _scaled_callback(0.05, 0.9, progress_callback)
        await translate_docx_file(input_path, output_path, llm_client, progress_callback=callback)
        if progress_callback:
            progress_callback(1.0, "DOCX translation completed")
        return output_path

    if ext == ".pptx":
        if progress_callback:
            progress_callback(0.05, "Analyzing PPTX slides")
        callback = _scaled_callback(0.05, 0.9, progress_callback)
        await translate_pptx_file(input_path, output_path, llm_client, progress_callback=callback)
        if progress_callback:
            progress_callback(1.0, "PPTX translation completed")
        return output_path

    raise UnsupportedFileTypeError(f"Unsupported file type: {ext}")
