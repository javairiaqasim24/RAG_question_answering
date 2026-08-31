"""Filesystem storage for uploaded documents, with filename sanitization."""
import re
import uuid
from pathlib import Path

from app.core.config import get_settings

settings = get_settings()

_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(filename: str) -> str:
    """Strip any path components and unsafe characters to prevent path traversal."""
    name = Path(filename).name  # drop any directory components
    name = _UNSAFE_CHARS.sub("_", name)
    name = name.strip("._") or "document.pdf"
    return name[:200]


def save_upload(document_id: str, filename: str, content: bytes) -> Path:
    """Save uploaded file bytes under a per-document directory and return the path."""
    safe_name = sanitize_filename(filename)
    doc_dir = settings.upload_path / document_id
    doc_dir.mkdir(parents=True, exist_ok=True)

    dest = (doc_dir / safe_name).resolve()
    if doc_dir.resolve() not in dest.parents and dest != doc_dir.resolve():
        # Defense in depth: should be unreachable given sanitize_filename above.
        raise ValueError("Resolved upload path escapes the document directory")

    dest.write_bytes(content)
    return dest


def new_document_id() -> str:
    return str(uuid.uuid4())


def delete_document_files(document_id: str) -> None:
    doc_dir = settings.upload_path / document_id
    if doc_dir.exists() and doc_dir.is_dir():
        for f in doc_dir.iterdir():
            f.unlink(missing_ok=True)
        doc_dir.rmdir()
