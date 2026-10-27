"""Immutable chunks and converted paper content."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class PaperChunk:
    """A source backed section of one paper version."""

    id: UUID
    paper_id: UUID
    content_version: int
    order_index: int
    markdown_text: str
    text_hash: str
    markdown_start: int
    markdown_end: int
