"""HTTP mapping for RubricService."""

from fastapi import APIRouter, Depends, Query, Response

from app.api.v1.schemas.rubrics import (
    RubricCreate,
    RubricPage,
    RubricRead,
    RubricUpdate,
)
from app.infrastructure.persistence.unit_of_work import UnitOfWork, get_uow
from app.services.rubric_service import RubricService

router = APIRouter(prefix="/api/v1/rubrics", tags=["rubrics"])


@router.post("", status_code=201, response_model=RubricRead)
def create_rubric(
    data: RubricCreate, response: Response, unit: UnitOfWork = Depends(get_uow)
):
    """Create an ordered qualitative rubric."""
    result = RubricService(unit.session).create(data)
    response.headers["Location"] = f"/api/v1/rubrics/{result.id}"
    return result


@router.get("", response_model=RubricPage)
def list_rubrics(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    unit: UnitOfWork = Depends(get_uow),
):
    """List active rubrics."""
    return RubricService(unit.session).list(limit, offset)


@router.get("/{rubric_id}", response_model=RubricRead)
def get_rubric(rubric_id: str, unit: UnitOfWork = Depends(get_uow)):
    """Read current rubric version."""
    return RubricService(unit.session).get(rubric_id)


@router.patch("/{rubric_id}", response_model=RubricRead)
def update_rubric(
    rubric_id: str, data: RubricUpdate, unit: UnitOfWork = Depends(get_uow)
):
    """Create a new rubric version."""
    return RubricService(unit.session).update(rubric_id, data)


@router.delete("/{rubric_id}", status_code=204)
def delete_rubric(rubric_id: str, unit: UnitOfWork = Depends(get_uow)):
    """Soft delete a rubric."""
    RubricService(unit.session).delete(rubric_id)
    return Response(status_code=204)
