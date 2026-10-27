"""Isolated API fixtures shared by run and report tests."""

from io import BytesIO

import pymupdf
import pytest
from fastapi.testclient import TestClient

from app.infrastructure.persistence.database import get_engine
from app.infrastructure.persistence.orm_models import Base
from app.main import app


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DEMO_LLM_MODE", "fixture")
    get_engine.cache_clear()
    Base.metadata.create_all(get_engine())
    yield TestClient(app)
    get_engine().dispose()
    get_engine.cache_clear()


@pytest.fixture
def review_seed(api_client):
    def create(with_reference=True):
        paper_ids = []
        for title, text in [
            ("Main study", "The sample contains 24 participants."),
            ("Related study", "The sample contains 40 participants."),
        ]:
            doc = pymupdf.open()
            doc.new_page().insert_text((72, 72), text)
            response = api_client.post(
                "/api/v1/papers",
                data={"title": title},
                files={
                    "file": ("paper.pdf", BytesIO(doc.tobytes()), "application/pdf")
                },
            )
            assert response.status_code == 201, response.text
            paper_ids.append(response.json()["id"])
        rubric = api_client.post(
            "/api/v1/rubrics",
            json={
                "name": "Default",
                "criteria": [{"code": "method", "question": "Assess sample"}],
            },
        )
        review = api_client.post(
            "/api/v1/reviews",
            json={
                "paper_id": paper_ids[0],
                "rubric_id": rubric.json()["id"],
                "reference_paper_ids": paper_ids[1:] if with_reference else [],
            },
        )
        assert review.status_code == 201
        return review.json()

    return create
