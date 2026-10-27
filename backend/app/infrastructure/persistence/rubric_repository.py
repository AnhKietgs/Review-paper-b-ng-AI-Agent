"""SQLAlchemy rubric adapter."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.infrastructure.persistence.orm_models import CriterionRow, RubricRow


class SqlRubricRepository:
    """Read and stage qualitative rubric versions."""

    def __init__(self, session: Session):
        self.session = session

    def get(self, rubric_id: str) -> RubricRow | None:
        """Read one active rubric."""
        return self.session.scalar(
            select(RubricRow).where(
                RubricRow.id == rubric_id,
                RubricRow.deleted_at.is_(None),
            )
        )

    def list(self, limit: int, offset: int) -> tuple[list[RubricRow], int]:
        """Paginate active rubric heads."""
        rows = list(
            self.session.scalars(
                select(RubricRow)
                .where(
                    RubricRow.deleted_at.is_(None),
                )
                .order_by(RubricRow.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        total = (
            self.session.scalar(
                select(func.count())
                .select_from(RubricRow)
                .where(
                    RubricRow.deleted_at.is_(None),
                )
            )
            or 0
        )
        return rows, total

    def criteria(self, rubric_id: str, version: int) -> list[CriterionRow]:
        """Read the criteria frozen in a rubric version."""
        return list(
            self.session.scalars(
                select(CriterionRow)
                .where(
                    CriterionRow.rubric_id == rubric_id,
                    CriterionRow.rubric_version == version,
                )
                .order_by(CriterionRow.order_index)
            )
        )
