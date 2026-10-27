"""SQLite engine and session factory."""

from functools import lru_cache

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings


@lru_cache(maxsize=1)
def get_engine():
    """Create one engine for the configured persistent data directory."""
    data_dir = Settings.from_env().data_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite:///{(data_dir / 'paper_review.sqlite3').as_posix()}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    return engine


def session_factory() -> sessionmaker:
    """Produce sessions without sharing transactions across requests."""
    return sessionmaker(bind=get_engine(), expire_on_commit=False)
