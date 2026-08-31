"""Page-aware PDF text extraction."""
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class PDFExtractionError(Exception):
    """Raised when a PDF cannot be parsed or contains no extractable text."""


@dataclass
class PageText:
    page_number: int  # 1-indexed
    text: str


def extract_pages(file_path: Path) -> list[PageText]:
    """Extract text from every page of a PDF, preserving page numbers.

    Raises PDFExtractionError for corrupted files or documents with no
    extractable text (e.g. scanned images with no OCR layer).
    """
    try:
        reader = PdfReader(str(file_path))
    except (PdfReadError, OSError) as exc:
        raise PDFExtractionError(f"Could not open PDF: {exc}") from exc

    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception as exc:  # noqa: BLE001
            raise PDFExtractionError("PDF is password-protected and cannot be read") from exc

    if len(reader.pages) == 0:
        raise PDFExtractionError("PDF contains no pages")

    pages: list[PageText] = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            raw_text = page.extract_text() or ""
        except Exception:  # noqa: BLE001 — pypdf can raise various parser errors per-page
            raw_text = ""
        pages.append(PageText(page_number=i, text=raw_text))

    if not any(p.text.strip() for p in pages):
        raise PDFExtractionError(
            "No extractable text found in PDF. It may be a scanned/image-only "
            "document that requires OCR, which this system does not currently support."
        )

    return pages
