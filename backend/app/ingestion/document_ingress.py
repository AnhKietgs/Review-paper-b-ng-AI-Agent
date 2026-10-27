"""Validate, convert and locate uploaded source documents."""

import hashlib
from pathlib import Path
from uuid import UUID

from app.domain.models.source import IngestedDocument
from app.ingestion.chunker import chunk_source
from app.ingestion.docx_locator import extract_docx_paragraphs
from app.ingestion.markitdown_adapter import MarkItDownAdapter
from app.ingestion.pdf_locator import extract_pdf_pages


class IngestionError(ValueError):
    """Unsupported or unreadable source file."""


class DocumentIngress:
    """Convert a document and keep defensible original locations."""

    def __init__(self, converter: MarkItDownAdapter | None = None):
        self.converter = converter or MarkItDownAdapter()

    def ingest(
        self,
        file_path: Path,
        paper_id: UUID,
        content_version: int,
    ) -> IngestedDocument:
        """Accept a text PDF or DOCX and return versioned chunks."""
        extension = file_path.suffix.lower()
        if extension not in {".pdf", ".docx"}:
            raise IngestionError("Only PDF and DOCX are supported")
        try:
            source_sections = (
                extract_pdf_pages(file_path)
                if extension == ".pdf"
                else extract_docx_paragraphs(file_path)
            )
        except Exception as exc:
            raise IngestionError("Cannot read the original document") from exc
        if not any(text.strip() for _, text, _ in source_sections):
            raise IngestionError("Document has no readable text layer")
        try:
            markdown = self.converter.convert(file_path)
        except Exception as exc:
            raise IngestionError("Document conversion failed") from exc
        if not markdown:
            raise IngestionError("Document conversion produced no text layer")
        source_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        chunks, locators = chunk_source(
            markdown,
            source_sections,
            paper_id,
            content_version,
            source_hash,
        )
        return IngestedDocument(markdown, chunks, locators, source_hash)
