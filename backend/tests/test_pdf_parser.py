import pytest

from app.ingestion.pdf_parser import PDFExtractionError, extract_pages
from tests.pdf_fixtures import empty_text_pdf_bytes, multi_page_pdf_bytes, valid_pdf_bytes


def _write(tmp_path, name, content):
    path = tmp_path / name
    path.write_bytes(content)
    return path


def test_extract_pages_returns_text_and_page_numbers(tmp_path):
    path = _write(tmp_path, "sample.pdf", valid_pdf_bytes("Hello World from a test PDF."))
    pages = extract_pages(path)
    assert len(pages) == 1
    assert pages[0].page_number == 1
    assert "Hello World" in pages[0].text


def test_extract_pages_handles_multiple_pages(tmp_path):
    path = _write(tmp_path, "multi.pdf", multi_page_pdf_bytes())
    pages = extract_pages(path)
    assert len(pages) == 2
    assert pages[0].page_number == 1
    assert pages[1].page_number == 2
    assert "mitochondria" in pages[0].text.lower()
    assert "retrieval" in pages[1].text.lower()


def test_extract_pages_raises_on_no_extractable_text(tmp_path):
    path = _write(tmp_path, "blank.pdf", empty_text_pdf_bytes())
    with pytest.raises(PDFExtractionError, match="No extractable text"):
        extract_pages(path)


def test_extract_pages_raises_on_corrupted_file(tmp_path):
    path = _write(tmp_path, "corrupt.pdf", b"this is not a real pdf file")
    with pytest.raises(PDFExtractionError):
        extract_pages(path)
