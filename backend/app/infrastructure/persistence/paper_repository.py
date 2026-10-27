"""SQLAlchemy implementation of PaperRepository."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.infrastructure.persistence.orm_models import (
    ChunkRow,
    LocatorRow,
    PaperRow,
)


class SqlPaperRepository:
    """Persist paper metadata and immutable content versions."""

    def __init__(self, session: Session):
        self.session = session

    def add(self, paper: PaperRow) -> None:
        """Stage a paper in the current transaction."""
        self.session.add(paper)

    def get(self, paper_id: str) -> PaperRow | None:
        """Return only nondeleted papers."""
        return self.session.scalar(
            select(PaperRow).where(
                PaperRow.id == paper_id,
                PaperRow.deleted_at.is_(None),
            )
        )

    def list(self, limit: int, offset: int) -> tuple[list[PaperRow], int]:
        """Return one page and its total."""
        query = select(PaperRow).where(PaperRow.deleted_at.is_(None))
        rows = list(
            self.session.scalars(
                query.order_by(PaperRow.created_at.desc()).limit(limit).offset(offset)
            )
        )
        count = (
            self.session.scalar(
                select(func.count())
                .select_from(PaperRow)
                .where(
                    PaperRow.deleted_at.is_(None),
                )
            )
            or 0
        )
        return rows, count

    def chunks(self, paper_id: str, version: int) -> list[ChunkRow]:
        """Get source chunks for a frozen version."""
        return list(
            self.session.scalars(
                select(ChunkRow)
                .where(
                    ChunkRow.paper_id == paper_id,
                    ChunkRow.content_version == version,
                )
                .order_by(ChunkRow.order_index)
            )
        )

    def locator(self, chunk_id: str) -> LocatorRow | None:
        """Read a chunk's source location."""
        return self.session.scalar(
            select(LocatorRow).where(
                LocatorRow.chunk_id == chunk_id,
            )
        )
