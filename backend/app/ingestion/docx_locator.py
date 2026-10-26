"""Independent DOCX paragraph location extraction."""

from pathlib import Path

from docx import Document


def extract_docx_paragraphs(path: Path) -> list[tuple[str, str, str]]:
    """Return one based paragraph index, text, and locator kind."""
    document = Document(path)
    return [
        (str(index + 1), paragraph.text.strip(), "docx_paragraph")
        for index, paragraph in enumerate(document.paragraphs)
        if paragraph.text.strip()
    ]

