"""Qualitative rubric CRUD and version snapshots."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.infrastructure.persistence.database import get_engine
from app.infrastructure.persistence.orm_models import Base, CriterionRow
from app.main import app


@pytest.fixture
def client(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    get_engine.cache_clear()
    Base.metadata.create_all(get_engine())
    yield TestClient(app)
    get_engine().dispose()
    get_engine.cache_clear()


def criterion(code: str, question: str) -> dict:
    return {"code": code, "question": question, "guidance": "Explain evidence"}


def test_rubric_crud_preserves_old_criteria(client: TestClient):
    created = client.post("/api/v1/rubrics", json={
        "name": "Methods rubric", "description": "Qualitative review",
        "criteria": [criterion("method", "Is the method clear?")],
    })
    assert created.status_code == 201, created.text
    rubric_id = created.json()["id"]
    assert created.headers["location"].endswith(rubric_id)
    assert client.get("/api/v1/rubrics").json()["total"] == 1
    assert client.get(f"/api/v1/rubrics/{rubric_id}").json()["version"] == 1

    changed = client.patch(f"/api/v1/rubrics/{rubric_id}", json={
        "criteria": [criterion("method", "Is the sample justified?"),
                     criterion("limits", "Are limitations clear?")],
    })
    assert changed.status_code == 200
    assert changed.json()["version"] == 2
    with get_engine().connect() as connection:
        versions = connection.execute(select(CriterionRow.rubric_version)).scalars().all()
    assert sorted(versions) == [1, 2, 2]

    assert client.delete(f"/api/v1/rubrics/{rubric_id}").status_code == 204
    assert client.get(f"/api/v1/rubrics/{rubric_id}").status_code == 404


def test_duplicate_criterion_code_is_invalid(client: TestClient):
    response = client.post("/api/v1/rubrics", json={
        "name": "Bad", "criteria": [criterion("x", "First"), criterion("x", "Second")],
    })
    assert response.status_code == 422
