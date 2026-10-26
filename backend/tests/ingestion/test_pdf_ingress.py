"""PDF conversion keeps independent source page evidence."""

from pathlib import Path
from uuid import uuid4

import fitz
import pytest

from app.ingestion.document_ingress import DocumentIngress, IngestionError


def make_pdf(path: Path, pages: list[str]) -> None:
    document = fitz.open()
    for text in pages:
        page = document.new_page()
        if text:
            page.insert_text((72, 72), text)
    document.save(path)


def test_pdf_page_two_is_original_source(tmp_path: Path):
    source = tmp_path / "paper.pdf"
    make_pdf(source, ["Introduction and methods.", "Distinct result on page two."])
    result = DocumentIngress().ingest(source, uuid4(), 1)
    assert "Distinct result" in result.markdown
    chunk = next(chunk for chunk in result.chunks if "Distinct result" in chunk.markdown_text)
    locator = next(item for item in result.locators if item.chunk_id == chunk.id)
    assert locator.locator_type == "pdf_page"
    assert locator.locator_value == "2"
    assert locator.status == "resolved"


def test_scanned_pdf_is_rejected(tmp_path: Path):
    source = tmp_path / "scanned.pdf"
    make_pdf(source, [""])
    with pytest.raises(IngestionError, match="text layer"):
        DocumentIngress().ingest(source, uuid4(), 1)


def test_duplicate_quote_cannot_be_safely_located(tmp_path: Path):
    source = tmp_path / "ambiguous.pdf"
    make_pdf(source, ["Identical finding.", "Identical finding."])
    result = DocumentIngress().ingest(source, uuid4(), 1)
    assert all(locator.status == "unresolved_locator" for locator in result.locators)

