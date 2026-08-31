import pytest

from app.services.validation import ValidationError, validate_upload


def test_rejects_non_pdf_extension():
    with pytest.raises(ValidationError, match="Unsupported file type"):
        validate_upload("notes.txt", "text/plain", 1000)


def test_rejects_empty_file():
    with pytest.raises(ValidationError, match="empty"):
        validate_upload("doc.pdf", "application/pdf", 0)


def test_rejects_oversized_file():
    with pytest.raises(ValidationError, match="maximum allowed size"):
        validate_upload("doc.pdf", "application/pdf", 999_999_999)


def test_accepts_valid_pdf():
    validate_upload("research-paper.pdf", "application/pdf", 50_000)  # should not raise


def test_rejects_missing_extension():
    with pytest.raises(ValidationError, match="extension"):
        validate_upload("noextension", "application/pdf", 1000)
