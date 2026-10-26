"""Pointers from a chunk back to the original file."""

from dataclasses import dataclass
from uuid import UUID

from app.domain.models.paper import PaperChunk


@dataclass(frozen=True)
class SourceLocator:
    """Stable page or paragraph location for an exact quote."""

    id: UUID
    chunk_id: UUID
    locator_type: str
    locator_value: str
    quote: str
    source_file_hash: str
    status: str


@dataclass(frozen=True)
class IngestedDocument:
    """Conversion output and independently extracted provenance."""

    markdown: str
    chunks: list[PaperChunk]
    locators: list[SourceLocator]
    source_file_hash: str

