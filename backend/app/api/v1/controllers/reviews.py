"""HTTP mapping for ReviewService."""

from fastapi import APIRouter, Depends, Query, Response

from app.api.v1.schemas.reviews import (
    ReviewCreate, ReviewPage, ReviewRead, ReviewUpdate,
)
from app.infrastructure.persistence.unit_of_work import UnitOfWork, get_uow
from app.services.review_service import ReviewService

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])


@router.post("", status_code=201, response_model=ReviewRead)
def create_review(data: ReviewCreate, response: Response,
                  unit: UnitOfWork = Depends(get_uow)):
    """Create a draft with manually selected references."""
    result = ReviewService(unit.session).create(data)
    response.headers["Location"] = f"/api/v1/reviews/{result.id}"
    return result


@router.get("", response_model=ReviewPage)
def list_reviews(limit: int = Query(20, ge=1, le=100),
                 offset: int = Query(0, ge=0),
                 unit: UnitOfWork = Depends(get_uow)):
    """List active review revisions."""
    return ReviewService(unit.session).list(limit, offset)


@router.get("/{review_id}", response_model=ReviewRead)
def get_review(review_id: str, unit: UnitOfWork = Depends(get_uow)):
    """Read one review revision."""
    return ReviewService(unit.session).get(review_id)


@router.patch("/{review_id}", response_model=ReviewRead)
def update_review(review_id: str, data: ReviewUpdate,
                  unit: UnitOfWork = Depends(get_uow)):
    """Edit a draft review."""
    return ReviewService(unit.session).update(review_id, data)


@router.post("/{review_id}/revisions", status_code=201, response_model=ReviewRead)
def new_review_revision(review_id: str, response: Response,
                        unit: UnitOfWork = Depends(get_uow)):
    """Fork the current revision into a new draft."""
    result = ReviewService(unit.session).new_revision(review_id)
    response.headers["Location"] = f"/api/v1/reviews/{result.id}"
    return result


@router.delete("/{review_id}", status_code=204)
def delete_review(review_id: str, unit: UnitOfWork = Depends(get_uow)):
    """Soft delete one review revision."""
    ReviewService(unit.session).delete(review_id)
    return Response(status_code=204)

