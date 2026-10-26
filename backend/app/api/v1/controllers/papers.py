"""HTTP mapping for PaperService."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, Request, Response, UploadFile
from fastapi.responses import FileResponse
from pydantic import ValidationError as PydanticValidationError

from app.api.v1.schemas.papers import PaperCreate, PaperPage, PaperRead, PaperUpdate
from app.core.errors import ValidationError
from app.infrastructure.persistence.unit_of_work import UnitOfWork, get_uow
from app.services.paper_service import PaperService

router = APIRouter(prefix="/api/v1/papers", tags=["papers"])


@router.post("", status_code=201, response_model=PaperRead)
def create_paper(
    response: Response,
    file: Annotated[UploadFile, File()],
    title: Annotated[str, Form()],
    authors: Annotated[str, Form()] = "",
    year: Annotated[int | None, Form()] = None,
    doi: Annotated[str | None, Form()] = None,
    unit: UnitOfWork = Depends(get_uow),
):
    """Create from multipart metadata and a source document."""
    try:
        metadata = PaperCreate(
            title=title, authors=[item.strip() for item in authors.split(",") if item.strip()],
            year=year, doi=doi,
        )
    except PydanticValidationError as exc:
        raise ValidationError("invalid_paper", str(exc)) from exc
    paper = PaperService(unit.session).create(file, metadata)
    response.headers["Location"] = f"/api/v1/papers/{paper.id}"
    return paper


@router.get("", response_model=PaperPage)
def list_papers(
    limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
    unit: UnitOfWork = Depends(get_uow),
):
    """List active library papers."""
    return PaperService(unit.session).list(limit, offset)


@router.get("/{paper_id}", response_model=PaperRead)
def get_paper(paper_id: str, unit: UnitOfWork = Depends(get_uow)):
    """Read one paper and its source locators."""
    return PaperService(unit.session).get(paper_id)


@router.get("/{paper_id}/source")
def get_paper_source(paper_id: str, unit: UnitOfWork = Depends(get_uow)):
    """Open the original source in the browser for checking evidence."""
    service = PaperService(unit.session)
    service.get(paper_id)
    row = service.repository.get(paper_id)
    return FileResponse(row.file_path, media_type=row.media_type,
                        filename=row.original_filename)


@router.patch("/{paper_id}", response_model=PaperRead)
async def update_paper(
    paper_id: str, request: Request, unit: UnitOfWork = Depends(get_uow),
):
    """Map JSON metadata or multipart replacement to PaperService."""
    content_type = request.headers.get("content-type", "")
    upload = None
    try:
        if content_type.startswith("multipart/form-data"):
            form = await request.form()
            upload = form.get("file")
            changes = PaperUpdate(**{
                key: form[key] for key in ("title", "doi") if key in form
            })
        else:
            changes = PaperUpdate.model_validate(await request.json())
    except (PydanticValidationError, ValueError) as exc:
        raise ValidationError("invalid_paper", str(exc)) from exc
    return PaperService(unit.session).update(paper_id, changes, upload)


@router.delete("/{paper_id}", status_code=204)
def delete_paper(paper_id: str, unit: UnitOfWork = Depends(get_uow)):
    """Soft delete a paper."""
    PaperService(unit.session).delete(paper_id)
    return Response(status_code=204)

