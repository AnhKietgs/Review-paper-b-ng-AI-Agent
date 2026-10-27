"""Relational model for versioned paper reviews."""

from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    """Return an aware UTC timestamp."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base for all persisted entities."""


class PaperRow(Base):
    """Paper metadata and current source version."""

    __tablename__ = "papers"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    authors: Mapped[list] = mapped_column(JSON, default=list)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    doi: Mapped[str | None] = mapped_column(String(255), nullable=True)
    original_filename: Mapped[str] = mapped_column(String(500))
    media_type: Mapped[str] = mapped_column(String(100))
    file_path: Mapped[str] = mapped_column(Text)
    markdown_path: Mapped[str] = mapped_column(Text)
    content_version: Mapped[int] = mapped_column(Integer, default=1)
    conversion_status: Mapped[str] = mapped_column(String(30), default="ready")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PaperVersionRow(Base):
    """Immutable original file and Markdown for historical source links."""

    __tablename__ = "paper_versions"
    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id"), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_path: Mapped[str] = mapped_column(Text)
    markdown_path: Mapped[str] = mapped_column(Text)
    original_filename: Mapped[str] = mapped_column(String(500))
    media_type: Mapped[str] = mapped_column(String(100))
    source_file_hash: Mapped[str] = mapped_column(String(64))


class ChunkRow(Base):
    """Immutable chunk for one paper content version."""

    __tablename__ = "paper_chunks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id"), index=True)
    content_version: Mapped[int] = mapped_column(Integer)
    order_index: Mapped[int] = mapped_column(Integer)
    markdown_text: Mapped[str] = mapped_column(Text)
    text_hash: Mapped[str] = mapped_column(String(64))
    markdown_start: Mapped[int] = mapped_column(Integer)
    markdown_end: Mapped[int] = mapped_column(Integer)


class LocatorRow(Base):
    """Source location resolved against the original upload."""

    __tablename__ = "source_locators"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    chunk_id: Mapped[str] = mapped_column(ForeignKey("paper_chunks.id"), index=True)
    locator_type: Mapped[str] = mapped_column(String(32))
    locator_value: Mapped[str] = mapped_column(String(100))
    quote: Mapped[str] = mapped_column(Text)
    source_file_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="resolved")


class RubricRow(Base):
    """Editable rubric head; criterion rows preserve old versions."""

    __tablename__ = "rubrics"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CriterionRow(Base):
    """One qualitative criterion of one rubric version."""

    __tablename__ = "criteria"
    __table_args__ = (UniqueConstraint("rubric_id", "rubric_version", "code"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    rubric_id: Mapped[str] = mapped_column(ForeignKey("rubrics.id"), index=True)
    rubric_version: Mapped[int] = mapped_column(Integer)
    code: Mapped[str] = mapped_column(String(64))
    question: Mapped[str] = mapped_column(Text)
    guidance: Mapped[str] = mapped_column(Text, default="")
    order_index: Mapped[int] = mapped_column(Integer)


class ReviewRow(Base):
    """A paper review draft or approved immutable revision."""

    __tablename__ = "reviews"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id"), index=True)
    paper_content_version: Mapped[int] = mapped_column(Integer)
    rubric_id: Mapped[str] = mapped_column(ForeignKey("rubrics.id"))
    rubric_version: Mapped[int] = mapped_column(Integer)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    parent_revision_id: Mapped[str | None] = mapped_column(String(36))
    status: Mapped[str] = mapped_column(String(32), default="draft")
    analysis: Mapped[dict] = mapped_column(JSON, default=dict)
    summary: Mapped[str] = mapped_column(Text, default="")
    reviewer_edits: Mapped[dict] = mapped_column(JSON, default=dict)
    approved_markdown: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ReviewReferenceRow(Base):
    """Selected reference and its frozen source version."""

    __tablename__ = "review_references"
    __table_args__ = (UniqueConstraint("review_id", "paper_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    review_id: Mapped[str] = mapped_column(ForeignKey("reviews.id"), index=True)
    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id"))
    paper_content_version: Mapped[int] = mapped_column(Integer)


class FindingRow(Base):
    """One review claim and its support state."""

    __tablename__ = "findings"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    review_id: Mapped[str] = mapped_column(ForeignKey("reviews.id"), index=True)
    criterion_code: Mapped[str] = mapped_column(String(64), default="general")
    kind: Mapped[str] = mapped_column(String(32), default="analysis")
    compared_paper_ids: Mapped[list] = mapped_column(JSON, default=list)
    claim: Mapped[str] = mapped_column(Text)
    evidence: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    verdict: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )


class RunRow(Base):
    """Background execution state."""

    __tablename__ = "runs"
    __table_args__ = (
        Index(
            "uq_runs_active_requested_review",
            "requested_review_id",
            unique=True,
            sqlite_where=text("status IN ('queued', 'running', 'interrupted')"),
            postgresql_where=text("status IN ('queued', 'running', 'interrupted')"),
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    review_id: Mapped[str] = mapped_column(ForeignKey("reviews.id"), index=True)
    requested_review_id: Mapped[str] = mapped_column(
        ForeignKey("reviews.id"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    status: Mapped[str] = mapped_column(String(32), default="queued")
    step_count: Mapped[int] = mapped_column(Integer, default=0)
    usage: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(64))


class RunEventRow(Base):
    """Ordered, secret free decision trace."""

    __tablename__ = "run_events"
    __table_args__ = (UniqueConstraint("run_id", "sequence"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    agent: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(64))
    tool: Mapped[str | None] = mapped_column(String(64))
    permission_result: Mapped[str | None] = mapped_column(String(32))
    input_summary: Mapped[str] = mapped_column(Text, default="")
    output_summary: Mapped[str] = mapped_column(Text, default="")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )


class RunCheckpointRow(Base):
    """Restartable harness state after each turn."""

    __tablename__ = "run_checkpoints"
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), primary_key=True)
    state_json: Mapped[dict] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
