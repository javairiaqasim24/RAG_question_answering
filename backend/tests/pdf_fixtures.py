"""Minimal raw-PDF builders for tests, avoiding a heavyweight PDF-authoring dependency."""


def _build_pdf(page_texts: list[str]) -> bytes:
    """Build a minimal, valid multi-page PDF with the given per-page text content."""
    objects: list[bytes] = []

    n_pages = len(page_texts)
    page_obj_start = 4  # objects: 1=Catalog, 2=Pages, 3=Font, 4..=Page/Content pairs

    kids = " ".join(f"{page_obj_start + 2 * i} 0 R" for i in range(n_pages))
    objects.append(b"<</Type/Catalog/Pages 2 0 R>>")  # 1
    objects.append(f"<</Type/Pages/Kids[{kids}]/Count {n_pages}>>".encode())  # 2
    objects.append(b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>")  # 3

    for text in page_texts:
        content_obj_num = page_obj_start + 2 * page_texts.index(text) + 1
        stream = f"BT /F1 24 Tf 72 700 Td ({text}) Tj ET".encode()
        page_dict = (
            f"<</Type/Page/Parent 2 0 R/Resources<</Font<</F1 3 0 R>>>>"
            f"/MediaBox[0 0 612 792]/Contents {content_obj_num} 0 R>>"
        ).encode()
        objects.append(page_dict)
        objects.append(b"<</Length " + str(len(stream)).encode() + b">>\nstream\n" + stream + b"\nendstream")

    header = b"%PDF-1.4\n"
    body = b""
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(header) + len(body))
        body += f"{i} 0 obj".encode() + b"\n" + obj + b"\nendobj\n"

    xref_offset = len(header) + len(body)
    n_objs = len(objects) + 1
    xref = f"xref\n0 {n_objs}\n0000000000 65535 f \n".encode()
    for off in offsets[1:]:
        xref += f"{off:010d} 00000 n \n".encode()

    trailer = (
        f"trailer\n<</Size {n_objs}/Root 1 0 R>>\nstartxref\n{xref_offset}\n%%EOF"
    ).encode()

    return header + body + xref + trailer


def valid_pdf_bytes(text: str = "Hello World from a test PDF.") -> bytes:
    return _build_pdf([text])


def multi_page_pdf_bytes() -> bytes:
    return _build_pdf(
        [
            "The mitochondria is the powerhouse of the cell.",
            "Retrieval augmented generation combines retrieval with generation.",
        ]
    )


def empty_text_pdf_bytes() -> bytes:
    """A structurally valid single blank page with no text content stream."""
    header = b"%PDF-1.4\n"
    objects = [
        b"<</Type/Catalog/Pages 2 0 R>>",
        b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
        b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>",
    ]
    body = b""
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(header) + len(body))
        body += f"{i} 0 obj".encode() + b"\n" + obj + b"\nendobj\n"
    xref_offset = len(header) + len(body)
    n_objs = len(objects) + 1
    xref = f"xref\n0 {n_objs}\n0000000000 65535 f \n".encode()
    for off in offsets:
        xref += f"{off:010d} 00000 n \n".encode()
    trailer = f"trailer\n<</Size {n_objs}/Root 1 0 R>>\nstartxref\n{xref_offset}\n%%EOF".encode()
    return header + body + xref + trailer
