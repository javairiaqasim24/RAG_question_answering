"""Recursive, boundary-aware text chunking.

Strategy: within each page, split preferentially on paragraph breaks, falling
back to sentence breaks, then word breaks, and finally raw characters if a
single unit is still too long. Chunks are built by greedily packing these
units up to `chunk_size` characters, with the last `chunk_overlap` characters
of each chunk repeated at the start of the next chunk so that context is not
lost at chunk boundaries.

Chunking is done per-page (rather than on the whole-document text) so every
chunk keeps a single, accurate page-number citation — the tradeoff is that a
paragraph split exactly across a page boundary becomes two chunks. This is
judged the better default for an academic QA tool where citation accuracy
matters more than the rare cross-page paragraph.
"""
from dataclasses import dataclass

_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


@dataclass
class Chunk:
    text: str
    page_number: int | None


def _split_on_separator(text: str, separator: str) -> list[str]:
    if separator == "":
        return list(text)
    parts = text.split(separator)
    # Re-attach the separator (except to the trailing empty split) so joined
    # length calculations and reconstructed text remain faithful.
    return [p + separator if i < len(parts) - 1 else p for i, p in enumerate(parts)]


def _recursive_split(text: str, chunk_size: int, separators: list[str]) -> list[str]:
    if len(text) <= chunk_size:
        return [text] if text else []

    if not separators:
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    sep, *rest = separators
    pieces = _split_on_separator(text, sep)

    results: list[str] = []
    for piece in pieces:
        if len(piece) <= chunk_size:
            results.append(piece)
        else:
            results.extend(_recursive_split(piece, chunk_size, rest))
    return results


def _pack_units(units: list[str], chunk_size: int, chunk_overlap: int) -> list[str]:
    """Greedily pack small units into chunks close to chunk_size, with overlap."""
    chunks: list[str] = []
    current = ""

    for unit in units:
        if current and len(current) + len(unit) > chunk_size:
            chunks.append(current.strip())
            # carry the overlap tail forward
            overlap_text = current[-chunk_overlap:] if chunk_overlap > 0 else ""
            current = overlap_text
        current += unit

    if current.strip():
        chunks.append(current.strip())

    return [c for c in chunks if c]


def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Split a single block of text into overlapping, boundary-aware chunks."""
    if not text or not text.strip():
        return []
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    units = _recursive_split(text, chunk_size, _SEPARATORS)
    return _pack_units(units, chunk_size, chunk_overlap)


def chunk_pages(
    pages: list[tuple[int, str]], chunk_size: int, chunk_overlap: int
) -> list[Chunk]:
    """Chunk a list of (page_number, cleaned_text) tuples, preserving page numbers."""
    chunks: list[Chunk] = []
    for page_number, page_text in pages:
        for piece in chunk_text(page_text, chunk_size, chunk_overlap):
            chunks.append(Chunk(text=piece, page_number=page_number))
    return chunks
