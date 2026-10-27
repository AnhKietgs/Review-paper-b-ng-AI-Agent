"""Paper CRUD, conversion and immutable content versions."""

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.api.v1.schemas.papers import PaperCreate, PaperRead, PaperUpdate
from app.core.errors import NotFoundError, ValidationError
from app.infrastructure.persistence.orm_models import (
    ChunkRow,
    LocatorRow,
    PaperRow,
    PaperVersionRow,
)
from app.infrastructure.persistence.paper_repository import SqlPaperRepository
from app.infrastructure.storage.local_files import LocalFileStore
from app.ingestion.document_ingress import DocumentIngress, IngestionError


class PaperService:
    """Own paper metadata and conversion transaction."""

    def __init__(self, session: Session):
        self.session = session
        self.repository = SqlPaperRepository(session)
        self.storage = LocalFileStore()
        self.ingress = DocumentIngress()

    @staticmethod
    def _validate_extension(upload: UploadFile) -> str:
        extension = Path(upload.filename or "").suffix.lower()
        if extension not in {".pdf", ".docx"}:
            raise ValidationError("unsupported_file", "Only PDF and DOCX are supported")
        return extension

    def _save_content(self, upload: UploadFile, paper: PaperRow, version: int) -> None:
        self._validate_extension(upload)
        path = self.storage.save_upload(upload, paper.id, version)
        try:
            result = self.ingress.ingest(path, UUID(paper.id), version)
        except IngestionError as exc:
            path.unlink(missing_ok=True)
            raise ValidationError("conversion_failed", str(exc)) from exc
        markdown_path = self.storage.save_markdown(result.markdown, paper.id, version)
        paper.original_filename = upload.filename or path.name
        paper.media_type = (
            "application/pdf"
            if path.suffix == ".pdf"
            else (
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            )
        )
        paper.file_path = str(path)
        paper.markdown_path = str(markdown_path)
        paper.content_version = version
        paper.conversion_status = "ready"
        self.session.add(
            PaperVersionRow(
                paper_id=paper.id,
                version=version,
                file_path=str(path),
                markdown_path=str(markdown_path),
                original_filename=paper.original_filename,
                media_type=paper.media_type,
                source_file_hash=result.source_file_hash,
            )
        )
        for chunk in result.chunks:
            self.session.add(
                ChunkRow(
                    id=str(chunk.id),
                    paper_id=paper.id,
                    content_version=chunk.content_version,
                    order_index=chunk.order_index,
                    markdown_text=chunk.markdown_text,
                    text_hash=chunk.text_hash,
                    markdown_start=chunk.markdown_start,
                    markdown_end=chunk.markdown_end,
                )
            )
        self.session.flush()
        for locator in result.locators:
            self.session.add(
                LocatorRow(
                    id=str(locator.id),
                    chunk_id=str(locator.chunk_id),
                    locator_type=locator.locator_type,
                    locator_value=locator.locator_value,
                    quote=locator.quote,
                    source_file_hash=locator.source_file_hash,
                    status=locator.status,
                )
            )

    def _read(self, row: PaperRow, detail: bool = False) -> PaperRead:
        markdown = (
            Path(row.markdown_path).read_text(encoding="utf-8")
            if detail and row.markdown_path
            else ""
        )
        chunks = []
        if detail:
            for chunk in self.repository.chunks(row.id, row.content_version):
                locator = self.repository.locator(chunk.id)
                chunks.append(
                    {
                        "id": chunk.id,
                        "text": chunk.markdown_text,
                        "content_version": chunk.content_version,
                        "locator": (
                            None
                            if locator is None
                            else {
                                "type": locator.locator_type,
                                "value": locator.locator_value,
                                "quote": locator.quote,
                                "status": locator.status,
                            }
                        ),
                    }
                )
        return PaperRead(
            id=row.id,
            title=row.title,
            authors=row.authors,
            year=row.year,
            doi=row.doi,
            original_filename=row.original_filename,
            media_type=row.media_type,
            content_version=row.content_version,
            conversion_status=row.conversion_status,
            markdown=markdown,
            chunks=chunks,
        )

    def create(self, upload: UploadFile, metadata: PaperCreate) -> PaperRead:
        """Create paper, convert it and stage all rows atomically."""
        self._validate_extension(upload)
        paper = PaperRow(
            id=str(uuid4()),
            title=metadata.title,
            authors=metadata.authors,
            year=metadata.year,
            doi=metadata.doi,
            original_filename="",
            media_type="",
            file_path="",
            markdown_path="",
            content_version=1,
            conversion_status="pending",
        )
        self.repository.add(paper)
        self.session.flush()
        self._save_content(upload, paper, 1)
        self.session.flush()
        return self._read(paper, detail=True)

    def get(self, paper_id: str) -> PaperRead:
        """Read active paper and its current chunks."""
        row = self.repository.get(paper_id)
        if row is None:
            raise NotFoundError("paper_missing", "Paper not found")
        return self._read(row, detail=True)

    def source(self, paper_id: str, version: int | None = None) -> PaperVersionRow:
        """Resolve a persisted source version, including archived references."""
        if version is None:
            version = self.get(paper_id).content_version
        source = self.session.get(PaperVersionRow, (paper_id, version))
        if source is None:
            raise NotFoundError("source_missing", "Source version not found")
        return source

    def get_version(self, paper_id: str, version: int) -> PaperRead:
        """Read exact historical content while retaining current metadata."""
        source = self.source(paper_id, version)
        row = self.session.get(PaperRow, paper_id)
        result = self._read(row)
        result.content_version = version
        result.original_filename = source.original_filename
        result.media_type = source.media_type
        result.markdown = Path(source.markdown_path).read_text(encoding="utf-8")
        result.chunks = []
        for chunk in self.repository.chunks(paper_id, version):
            locator = self.repository.locator(chunk.id)
            result.chunks.append(
                {
                    "id": chunk.id,
                    "text": chunk.markdown_text,
                    "content_version": version,
                    "locator": {
                        "type": locator.locator_type,
                        "value": locator.locator_value,
                        "status": locator.status,
                    },
                }
            )
        return result

    def list(self, limit: int, offset: int) -> dict:
        """Return paginated active papers."""
        rows, total = self.repository.list(limit, offset)
        return {
            "items": [self._read(row) for row in rows],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def update(
        self, paper_id: str, changes: PaperUpdate, upload: UploadFile | None = None
    ) -> PaperRead:
        """Change metadata or create a new immutable source version."""
        row = self.repository.get(paper_id)
        if row is None:
            raise NotFoundError("paper_missing", "Paper not found")
        for key, value in changes.model_dump(exclude_unset=True).items():
            setattr(row, key, value)
        if upload is not None:
            self._save_content(upload, row, row.content_version + 1)
        self.session.flush()
        return self._read(row, detail=True)

    def delete(self, paper_id: str) -> None:
        """Soft delete while preserving references from existing reviews."""
        row = self.repository.get(paper_id)
        if row is None:
            raise NotFoundError("paper_missing", "Paper not found")
        row.deleted_at = datetime.now(timezone.utc)
