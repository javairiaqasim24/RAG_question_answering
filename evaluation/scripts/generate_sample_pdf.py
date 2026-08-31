"""Generate the sample PDF used for development, testing, and evaluation.

Renders sample_docs/sample_document_source.txt (an original primer on RAG,
written for this project) into sample_docs/rag_primer.pdf, one page per
"===PAGE N===" marker in the source file, so page numbers line up exactly
with evaluation/datasets/qa_dataset.json's ground-truth citations.
"""
from pathlib import Path
from textwrap import wrap

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SOURCE_PATH = REPO_ROOT / "sample_docs" / "sample_document_source.txt"
OUTPUT_PATH = REPO_ROOT / "sample_docs" / "rag_primer.pdf"

MARGIN = 72
FONT = "Helvetica"
BODY_SIZE = 11
LEADING = 15
WRAP_WIDTH = 92


_ASCII_FALLBACKS = {
    "—": "-",  # em dash
    "–": "-",  # en dash
    "‘": "'",
    "’": "'",
    "“": '"',
    "”": '"',
}


def _sanitize(text: str) -> str:
    for src, dst in _ASCII_FALLBACKS.items():
        text = text.replace(src, dst)
    return text


def parse_pages(text: str) -> list[str]:
    pages = text.split("===PAGE")
    return [_sanitize(p.split("===", 1)[1].strip()) for p in pages if p.strip()]


def draw_page(c: canvas.Canvas, content: str) -> None:
    width, height = LETTER
    y = height - MARGIN
    c.setFont(FONT, BODY_SIZE)

    paragraphs = content.strip().split("\n\n")
    title = paragraphs[0].strip()
    body_paragraphs = paragraphs[1:]

    c.setFont(FONT + "-Bold", 16)
    for line in wrap(title, 60):
        c.drawString(MARGIN, y, line)
        y -= 22
    y -= 8
    c.setFont(FONT, BODY_SIZE)

    for para in body_paragraphs:
        for line in wrap(" ".join(para.split()), WRAP_WIDTH):
            if y < MARGIN:
                c.showPage()
                c.setFont(FONT, BODY_SIZE)
                y = height - MARGIN
            c.drawString(MARGIN, y, line)
            y -= LEADING
        y -= LEADING  # paragraph spacing


def main() -> None:
    text = SOURCE_PATH.read_text(encoding="utf-8")
    pages = parse_pages(text)

    c = canvas.Canvas(str(OUTPUT_PATH), pagesize=LETTER)
    for page_content in pages:
        draw_page(c, page_content)
        c.showPage()
    c.save()
    print(f"Wrote {len(pages)}-page PDF to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
