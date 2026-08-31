"""Text normalization applied to raw PDF-extracted text before chunking."""
import re

_MULTI_SPACE = re.compile(r"[ \t]+")
_MULTI_BLANK_LINES = re.compile(r"\n{3,}")
_HYPHEN_LINEBREAK = re.compile(r"(\w)-\n(\w)")  # de-hyphenate words split across lines


def clean_text(text: str) -> str:
    """Normalize whitespace and repair common PDF-extraction artifacts."""
    if not text:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _HYPHEN_LINEBREAK.sub(r"\1\2", text)
    text = _MULTI_SPACE.sub(" ", text)
    text = _MULTI_BLANK_LINES.sub("\n\n", text)
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)
    return text.strip()
