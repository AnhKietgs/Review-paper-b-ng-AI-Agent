"""Independent PDF page text extraction."""

from pathlib import Path

import pymupdf


def extract_pdf_pages(path: Path) -> list[tuple[str, str, str]]:
    """Return page number, page text, and locator kind."""
    with pymupdf.open(stream=path.read_bytes(), filetype="pdf") as document:
        return [
            (str(index + 1), page.get_text("text").strip(), "pdf_page")
            for index, page in enumerate(document)
        ]
