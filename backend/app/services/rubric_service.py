"""Rubric CRUD and immutable criterion versions."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.api.v1.schemas.rubrics import (
    CriterionInput,
    CriterionRead,
    RubricCreate,
    RubricRead,
    RubricUpdate,
)
from app.core.errors import NotFoundError
from app.infrastructure.persistence.orm_models import CriterionRow, RubricRow
from app.infrastructure.persistence.rubric_repository import SqlRubricRepository


class RubricService:
    """Apply rubric changes while retaining earlier criteria."""

    def __init__(self, session: Session):
        self.session = session
        self.repository = SqlRubricRepository(session)

    def _write_criteria(
        self, rubric_id: str, version: int, criteria: list[CriterionInput]
    ) -> None:
        for index, item in enumerate(criteria):
            self.session.add(
                CriterionRow(
                    id=str(uuid4()),
                    rubric_id=rubric_id,
                    rubric_version=version,
                    code=item.code,
                    question=item.question,
                    guidance=item.guidance,
                    order_index=index,
                )
            )

    def _read(self, row: RubricRow) -> RubricRead:
        criteria = [
            CriterionRead(
                code=item.code,
                question=item.question,
                guidance=item.guidance,
                order_index=item.order_index,
            )
            for item in self.repository.criteria(row.id, row.version)
        ]
        return RubricRead(
            id=row.id,
            name=row.name,
            description=row.description,
            version=row.version,
            criteria=criteria,
        )

    def create(self, data: RubricCreate) -> RubricRead:
        """Create a qualitative rubric at version one."""
        row = RubricRow(
            id=str(uuid4()), name=data.name, description=data.description, version=1
        )
        self.session.add(row)
        self.session.flush()
        self._write_criteria(row.id, 1, data.criteria)
        self.session.flush()
        return self._read(row)

    def get(self, rubric_id: str) -> RubricRead:
        """Read an active rubric."""
        row = self.repository.get(rubric_id)
        if row is None:
            raise NotFoundError("rubric_missing", "Rubric not found")
        return self._read(row)

    def list(self, limit: int, offset: int) -> dict:
        """Return one page of active rubrics."""
        rows, total = self.repository.list(limit, offset)
        return {
            "items": [self._read(row) for row in rows],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def update(self, rubric_id: str, data: RubricUpdate) -> RubricRead:
        """Advance version and copy unchanged criteria into the new version."""
        row = self.repository.get(rubric_id)
        if row is None:
            raise NotFoundError("rubric_missing", "Rubric not found")
        previous = self.repository.criteria(row.id, row.version)
        criteria = data.criteria or [
            CriterionInput(
                code=item.code,
                question=item.question,
                guidance=item.guidance,
            )
            for item in previous
        ]
        if data.name is not None:
            row.name = data.name
        if data.description is not None:
            row.description = data.description
        row.version += 1
        self._write_criteria(row.id, row.version, criteria)
        self.session.flush()
        return self._read(row)

    def delete(self, rubric_id: str) -> None:
        """Soft delete without invalidating existing review snapshots."""
        row = self.repository.get(rubric_id)
        if row is None:
            raise NotFoundError("rubric_missing", "Rubric not found")
        row.deleted_at = datetime.now(timezone.utc)
