"""Idempotent sample library creation through application services."""

import json
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.schemas.papers import PaperCreate
from app.api.v1.schemas.rubrics import CriterionInput, RubricCreate
from app.infrastructure.persistence.orm_models import PaperRow, RubricRow
from app.infrastructure.persistence.unit_of_work import UnitOfWork
from app.services.paper_service import PaperService
from app.services.rubric_service import RubricService


def seed(session: Session, assets: Path) -> dict:
    """Create missing demo records without overwriting user edits."""
    ids = []
    for filename, title in [
        ("main_sample.pdf", "Demo · Evidence Links Pilot"),
        ("related_sample.docx", "Demo · Related Study"),
    ]:
        existing = session.scalar(
            select(PaperRow).where(
                PaperRow.title == title, PaperRow.deleted_at.is_(None)
            )
        )
        if existing is None:
            with (assets / filename).open("rb") as source:
                paper = PaperService(session).create(
                    UploadFile(filename=filename, file=source), PaperCreate(title=title)
                )
                ids.append(paper.id)
        else:
            ids.append(existing.id)
    rubric = session.scalar(
        select(RubricRow).where(
            RubricRow.name == "Demo · Scientific Review", RubricRow.deleted_at.is_(None)
        )
    )
    if rubric is None:
        rubric = RubricService(session).create(
            RubricCreate(
                name="Demo · Scientific Review",
                description="Qualitative review of methods, evidence and limitations.",
                criteria=[
                    CriterionInput(code=code, question=question)
                    for code, question in [
                        (
                            "methodology",
                            "Is the methodology supported by the reported design?",
                        ),
                        ("evidence", "What evidence supports the reported results?"),
                        (
                            "limitations",
                            "Which limitations are acknowledged or not addressed?",
                        ),
                    ]
                ],
            )
        )
    return {"paper_id": ids[0], "rubric_id": rubric.id, "reference_paper_ids": ids[1:]}


def main() -> None:
    """Seed from the Compose read-only mount or repository demo directory."""
    mounted = Path("/app/demo_data")
    assets = (
        mounted
        if mounted.exists()
        else Path(__file__).resolve().parents[3] / "demo_data"
    )
    with UnitOfWork() as unit:
        result = seed(unit.session, assets)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
