"""Upload validation: file type, size, and basic content sanity checks."""
from app.core.config import get_settings

settings = get_settings()

ALLOWED_CONTENT_TYPES = {"application/pdf"}
ALLOWED_EXTENSIONS = {".pdf"}


class ValidationError(Exception):
    pass


def validate_upload(filename: str, content_type: str | None, size_bytes: int) -> None:
    if not filename or "." not in filename:
        raise ValidationError("Filename is missing a file extension.")

    ext = "." + filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file type '{ext}'. Only PDF files are currently supported."
        )

    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        raise ValidationError(
            f"Unsupported content type '{content_type}'. Expected application/pdf."
        )

    if size_bytes <= 0:
        raise ValidationError("Uploaded file is empty.")

    if size_bytes > settings.max_file_size_bytes:
        raise ValidationError(
            f"File exceeds the maximum allowed size of {settings.max_file_size_mb}MB."
        )
