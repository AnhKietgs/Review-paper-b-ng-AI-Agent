"""REST failure shape and initial database migration."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.main import register_error_handlers


def test_domain_errors_map_to_rest_status():
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/{kind}")
    def raise_domain_error(kind: str):
        if kind == "missing":
            raise NotFoundError("paper_missing", "Paper not found")
        if kind == "conflict":
            raise ConflictError("review_locked", "Review is locked")
        raise ValidationError("invalid_reference", "Bad reference")

    client = TestClient(app)
    for kind, status, code in [
        ("missing", 404, "paper_missing"),
        ("conflict", 409, "review_locked"),
        ("invalid", 422, "invalid_reference"),
    ]:
        response = client.get(f"/{kind}")
        assert response.status_code == status
        assert response.json() == {
            "code": code,
            "detail": response.json()["detail"],
        }


def test_migration_creates_core_tables(tmp_path: Path):
    database_url = f"sqlite:///{tmp_path / 'fresh.sqlite3'}"
    config = Config(str(Path(__file__).parents[2] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).parents[2] / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")
    tables = set(inspect(create_engine(database_url)).get_table_names())
    assert {
        "papers", "paper_chunks", "source_locators", "rubrics", "criteria",
        "reviews", "review_references", "findings", "runs", "run_events",
        "run_checkpoints",
    } <= tables
