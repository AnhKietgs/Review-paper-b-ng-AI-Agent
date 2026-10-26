"""SQLAlchemy review adapter."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.infrastructure.persistence.orm_models import (
    FindingRow, ReviewReferenceRow, ReviewRow,
)


class SqlReviewRepository:
    """Read review revisions, selected references and findings."""

    def __init__(self, session: Session):
        self.session = session

    def get(self, review_id: str) -> ReviewRow | None:
        """Read an active review revision."""
        return self.session.scalar(select(ReviewRow).where(
            ReviewRow.id == review_id, ReviewRow.deleted_at.is_(None),
        ))

    def list(self, limit: int, offset: int) -> tuple[list[ReviewRow], int]:
        """Paginate active review revisions."""
        rows = list(self.session.scalars(select(ReviewRow).where(
            ReviewRow.deleted_at.is_(None),
        ).order_by(ReviewRow.created_at.desc()).limit(limit).offset(offset)))
        total = self.session.scalar(select(func.count()).select_from(ReviewRow).where(
            ReviewRow.deleted_at.is_(None),
        )) or 0
        return rows, total

    def references(self, review_id: str) -> list[ReviewReferenceRow]:
        """Read frozen related paper scope."""
        return list(self.session.scalars(select(ReviewReferenceRow).where(
            ReviewReferenceRow.review_id == review_id,
        ).order_by(ReviewReferenceRow.paper_id)))

    def findings(self, review_id: str) -> list[FindingRow]:
        """Read draft findings in stable order."""
        return list(self.session.scalars(select(FindingRow).where(
            FindingRow.review_id == review_id,
        ).order_by(FindingRow.created_at, FindingRow.id)))

