"""Read-only source catalog behind the harness gateway."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.persistence.orm_models import ChunkRow, LocatorRow, PaperRow
from app.infrastructure.persistence.rubric_repository import SqlRubricRepository


class SqlSourceCatalog:
    """Expose source evidence with immutable paper/version identity."""

    def __init__(self, session: Session):
        self.session = session

    def is_active(self, paper_id: str) -> bool:
        """Deleted papers are not available to fresh tool calls."""
        row = self.session.get(PaperRow, paper_id)
        return row is not None and row.deleted_at is None

    def chunk(self, chunk_id: str) -> dict | None:
        """Read a source chunk and its independent locator."""
        row = self.session.get(ChunkRow, chunk_id)
        if row is None:
            return None
        locator = self.session.scalar(
            select(LocatorRow).where(LocatorRow.chunk_id == chunk_id)
        )
        return {
            "id": row.id,
            "paper_id": row.paper_id,
            "content_version": row.content_version,
            "text": row.markdown_text,
            "locator": (
                None
                if locator is None
                else {
                    "type": locator.locator_type,
                    "value": locator.locator_value,
                    "status": locator.status,
                    "source_file_hash": locator.source_file_hash,
                }
            ),
        }

    def chunks(self, paper_id: str, version: int) -> list[dict]:
        """Read chunks from one exact content version."""
        ids = self.session.scalars(
            select(ChunkRow.id)
            .where(
                ChunkRow.paper_id == paper_id,
                ChunkRow.content_version == version,
            )
            .order_by(ChunkRow.order_index)
        )
        return [self.chunk(chunk_id) for chunk_id in ids]

    def criteria(self, rubric_id: str, version: int) -> list[dict]:
        """Read qualitative strategy criteria for the frozen rubric."""
        return [
            {"code": row.code, "question": row.question, "guidance": row.guidance}
            for row in SqlRubricRepository(self.session).criteria(rubric_id, version)
        ]
