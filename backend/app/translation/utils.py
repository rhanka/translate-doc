from __future__ import annotations

import html
import itertools
import re
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

from docx.enum.text import WD_COLOR_INDEX
from docx.shared import Pt as DocxPt
from docx.shared import RGBColor
from pptx.dml.color import RGBColor as PPTXRGBColor
from pptx.util import Pt as PptxPt

TAG_PATTERN = re.compile(r"<(?P<key>s\d+?)>(?P<text>.*?)</\1>", re.DOTALL)
PARAGRAPH_DELIMITER = "[--translate-doc-paragraph-break--]"


@dataclass(slots=True)
class RunFormatting:
    bold: bool | None
    italic: bool | None
    underline: bool | None
    font_name: str | None
    font_size: float | None
    font_color: str | None
    highlight_color: int | None

    @classmethod
    def from_docx_run(cls, run) -> "RunFormatting":
        font = run.font
        size = float(font.size.pt) if font.size else None
        color = font.color.rgb if font.color and font.color.rgb else None
        highlight = font.highlight_color if getattr(font, "highlight_color", None) else None
        # Handle RGBColor object properly
        if color is not None:
            if hasattr(color, 'rgb'):
                # RGBColor object - access the rgb property
                color_hex = f"{color.rgb:06X}"
            else:
                # RGBColor object - unpack RGB values and convert to hex
                r, g, b = color
                color_hex = f"{r:02X}{g:02X}{b:02X}"
        else:
            color_hex = None
        highlight_value = int(highlight) if highlight is not None else None
        return cls(
            bold=run.bold,
            italic=run.italic,
            underline=run.underline,
            font_name=font.name,
            font_size=size,
            font_color=color_hex,
            highlight_color=highlight_value,
        )

    @classmethod
    def from_pptx_run(cls, run) -> "RunFormatting":
        font = run.font
        size = float(font.size.pt) if font.size else None
        color = font.color.rgb if font.color and font.color.rgb else None
        color_hex = f"{int(color):06X}" if color is not None else None
        return cls(
            bold=font.bold,
            italic=font.italic,
            underline=font.underline,
            font_name=font.name,
            font_size=size,
            font_color=color_hex,
            highlight_color=None,
        )

    def apply_to_docx_run(self, run) -> None:
        run.bold = self.bold
        run.italic = self.italic
        run.underline = self.underline
        font = run.font
        if self.font_name is not None:
            font.name = self.font_name
        if self.font_size is not None:
            font.size = DocxPt(self.font_size)
        if self.font_color is not None:
            font.color.rgb = RGBColor.from_string(self.font_color)
        if self.highlight_color is not None:
            font.highlight_color = WD_COLOR_INDEX(self.highlight_color)

    def apply_to_pptx_run(self, run) -> None:
        font = run.font
        font.bold = self.bold
        font.italic = self.italic
        font.underline = self.underline
        if self.font_name is not None:
            font.name = self.font_name
        if self.font_size is not None:
            font.size = PptxPt(self.font_size)
        if self.font_color is not None:
            font.color.rgb = PPTXRGBColor.from_string(self.font_color)


class StylePalette:
    def __init__(self) -> None:
        self._styles: dict[str, RunFormatting] = {}
        self._signatures: dict[tuple, str] = {}

    def register_docx_run(self, run) -> str:
        fmt = RunFormatting.from_docx_run(run)
        return self._register(fmt)

    def register_pptx_run(self, run) -> str:
        fmt = RunFormatting.from_pptx_run(run)
        return self._register(fmt)

    def _register(self, fmt: RunFormatting) -> str:
        signature = (
            fmt.bold,
            fmt.italic,
            fmt.underline,
            fmt.font_name,
            fmt.font_size,
            fmt.font_color,
            fmt.highlight_color,
        )
        if signature in self._signatures:
            return self._signatures[signature]
        key = f"s{len(self._styles) + 1}"
        self._styles[key] = fmt
        self._signatures[signature] = key
        return key

    def apply_docx(self, key: str, run) -> None:
        fmt = self._styles[key]
        fmt.apply_to_docx_run(run)

    def apply_pptx(self, key: str, run) -> None:
        fmt = self._styles[key]
        fmt.apply_to_pptx_run(run)

    def keys(self) -> Iterable[str]:
        return self._styles.keys()

    def has(self, key: str) -> bool:
        return key in self._styles


def escape_text(text: str) -> str:
    return html.escape(text, quote=False)


def unescape_text(text: str) -> str:
    return html.unescape(text)


def iter_tagged_segments(payload: str) -> List[Tuple[str, str]]:
    segments: List[Tuple[str, str]] = []
    for match in TAG_PATTERN.finditer(payload):
        segments.append((match.group("key"), match.group("text")))
    return segments


def chunked(sequence: Sequence, size: int) -> Iterable[Sequence]:
    it = iter(sequence)
    while True:
        chunk = list(itertools.islice(it, size))
        if not chunk:
            break
        yield chunk
