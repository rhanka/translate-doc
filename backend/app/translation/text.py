from __future__ import annotations

from pathlib import Path

TEXT_SYSTEM_PROMPT = (
    "You are a professional translator. Translate the provided text to French while "
    "preserving markdown or plaintext structure."
)


async def translate_text_file(input_path: Path, output_path: Path, llm_client) -> None:
    text = input_path.read_text(encoding="utf-8")
    translated = await llm_client.translate(system_prompt=TEXT_SYSTEM_PROMPT, user_prompt=text)
    output_path.write_text(translated, encoding="utf-8")
