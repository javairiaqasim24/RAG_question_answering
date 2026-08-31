from app.ingestion.cleaner import clean_text


def test_clean_text_collapses_whitespace():
    assert clean_text("hello    world") == "hello world"


def test_clean_text_dehyphenates_line_breaks():
    assert clean_text("infor-\nmation") == "information"


def test_clean_text_collapses_blank_lines():
    result = clean_text("para one\n\n\n\n\npara two")
    assert "\n\n\n" not in result


def test_clean_text_handles_empty_input():
    assert clean_text("") == ""
    assert clean_text(None) == ""  # type: ignore[arg-type]
