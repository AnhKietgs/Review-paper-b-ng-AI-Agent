"""Paper HTTP schemas."""

from pydantic import BaseModel, ConfigDict, Field


class PaperCreate(BaseModel):
    """Metadata accepted with an uploaded source."""

    title: str = Field(min_length=1, max_length=500)
    authors: list[str] = Field(default_factory=list)
    year: int | None = Field(default=None, ge=1800, le=2200)
    doi: str | None = None


class PaperUpdate(BaseModel):
    """Partial metadata update."""

    title: str | None = Field(default=None, min_length=1, max_length=500)
    authors: list[str] | None = None
    year: int | None = Field(default=None, ge=1800, le=2200)
    doi: str | None = None


class PaperRead(BaseModel):
    """Paper metadata and current converted content."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    authors: list[str]
    year: int | None
    doi: str | None
    original_filename: str
    media_type: str
    content_version: int
    conversion_status: str
    markdown: str = ""
    chunks: list[dict] = Field(default_factory=list)


class PaperPage(BaseModel):
    """Paginated paper collection."""

    items: list[PaperRead]
    total: int
    limit: int
    offset: int
