"""DOCX evidence points to source paragraphs."""

from pathlib import Path
from uuid import uuid4

from docx import Document

from app.ingestion.document_ingress import DocumentIngress


def test_docx_paragraph_three_is_original_source(tmp_path: Path):
    source = tmp_path / "related.docx"
    document = Document()
    for text in ("Related study", "Methods used a cohort.",
                 "The third paragraph reports a clear result."):
        document.add_paragraph(text)
    document.save(source)
    result = DocumentIngress().ingest(source, uuid4(), 2)
    chunk = next(chunk for chunk in result.chunks if "third paragraph" in chunk.markdown_text)
    locator = next(item for item in result.locators if item.chunk_id == chunk.id)
    assert locator.locator_type == "docx_paragraph"
    assert locator.locator_value == "3"
    assert chunk.content_version == 2

