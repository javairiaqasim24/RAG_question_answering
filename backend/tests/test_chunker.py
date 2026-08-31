import pytest

from app.ingestion.chunker import chunk_pages, chunk_text


def test_chunk_text_returns_empty_for_blank_input():
    assert chunk_text("", chunk_size=100, chunk_overlap=10) == []
    assert chunk_text("   \n  ", chunk_size=100, chunk_overlap=10) == []


def test_chunk_text_respects_max_size_roughly():
    text = "word " * 500  # 2500 chars
    chunks = chunk_text(text, chunk_size=200, chunk_overlap=20)
    assert len(chunks) > 1
    # Allow small slack since splitting happens on word boundaries.
    assert all(len(c) <= 220 for c in chunks)


def test_chunk_text_preserves_all_content_words():
    text = "Alpha bravo charlie. Delta echo foxtrot. " * 20
    chunks = chunk_text(text, chunk_size=100, chunk_overlap=15)
    reconstructed = " ".join(chunks)
    assert "Alpha" in reconstructed
    assert "foxtrot" in reconstructed


def test_chunk_text_overlap_carries_context_between_chunks():
    text = "sentence number " * 300
    chunks = chunk_text(text, chunk_size=150, chunk_overlap=30)
    assert len(chunks) >= 2
    # The tail of chunk[i] should share some text with the head of chunk[i+1].
    tail = chunks[0][-20:]
    assert any(tail[:10] in chunks[i] for i in range(1, len(chunks)))


def test_chunk_text_rejects_overlap_larger_than_size():
    with pytest.raises(ValueError):
        chunk_text("some text", chunk_size=50, chunk_overlap=50)


def test_chunk_pages_preserves_page_numbers():
    pages = [(1, "First page content. " * 10), (2, "Second page content. " * 10)]
    chunks = chunk_pages(pages, chunk_size=100, chunk_overlap=10)
    assert any(c.page_number == 1 for c in chunks)
    assert any(c.page_number == 2 for c in chunks)
    # No chunk should mix text across pages.
    for c in chunks:
        if c.page_number == 1:
            assert "Second" not in c.text
        if c.page_number == 2:
            assert "First" not in c.text
