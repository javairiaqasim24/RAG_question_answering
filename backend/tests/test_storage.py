from app.services.storage import sanitize_filename


def test_sanitize_filename_strips_path_components():
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert sanitize_filename("..\\..\\windows\\system32\\evil.pdf") == "evil.pdf"


def test_sanitize_filename_strips_unsafe_characters():
    result = sanitize_filename("my report (final)!.pdf")
    assert " " not in result
    assert "(" not in result
    assert result.endswith(".pdf")


def test_sanitize_filename_handles_empty_result():
    result = sanitize_filename("...")
    assert result == "document.pdf"
