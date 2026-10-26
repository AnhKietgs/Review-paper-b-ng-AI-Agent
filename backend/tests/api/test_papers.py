"""Paper REST CRUD and immutable source versions."""

from io import BytesIO
from pathlib import Path

import pymupdf
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.infrastructure.persistence.database import get_engine
from app.infrastructure.persistence.orm_models import Base, ChunkRow
from app.main import app


def pdf_bytes(text: str) -> bytes:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    return document.tobytes()


@pytest.fixture
def client(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    get_engine.cache_clear()
    Base.metadata.create_all(get_engine())
    yield TestClient(app)
    get_engine().dispose()
    get_engine.cache_clear()


def test_paper_crud_and_content_versions(client: TestClient):
    created = client.post(
        "/api/v1/papers",
        data={"title": "A main paper", "authors": "Alice, Bob"},
        files={"file": ("paper.pdf", BytesIO(pdf_bytes("Original evidence.")),
                        "application/pdf")},
    )
    assert created.status_code == 201, created.text
    paper_id = created.json()["id"]
    assert created.headers["location"].endswith(f"/papers/{paper_id}")
    assert client.get("/api/v1/papers").json()["total"] == 1
    assert client.get(f"/api/v1/papers/{paper_id}").json()["markdown"]

    renamed = client.patch(f"/api/v1/papers/{paper_id}", json={"title": "Renamed"})
    assert renamed.status_code == 200
    assert renamed.json()["content_version"] == 1

    replaced = client.patch(
        f"/api/v1/papers/{paper_id}",
        files={"file": ("new.pdf", BytesIO(pdf_bytes("New evidence.")),
                        "application/pdf")},
    )
    assert replaced.status_code == 200, replaced.text
    assert replaced.json()["content_version"] == 2
    with get_engine().connect() as connection:
        versions = connection.execute(select(ChunkRow.content_version)).scalars().all()
    assert set(versions) == {1, 2}

    assert client.delete(f"/api/v1/papers/{paper_id}").status_code == 204
    assert client.get(f"/api/v1/papers/{paper_id}").status_code == 404
    assert client.get("/api/v1/papers").json()["total"] == 0


def test_rejects_unsupported_upload(client: TestClient):
    response = client.post(
        "/api/v1/papers", data={"title": "Bad"},
        files={"file": ("bad.txt", b"text", "text/plain")},
    )
    assert response.status_code == 422
