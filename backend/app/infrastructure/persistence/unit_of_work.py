"""Transaction boundary shared by application services."""

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.infrastructure.persistence.database import session_factory


class UnitOfWork:
    """One database transaction for one use case."""

    def __init__(self, session: Session | None = None):
        self.session = session or session_factory()()
        self._owned = session is None

    def __enter__(self) -> "UnitOfWork":
        return self

    def __exit__(self, exc_type, _exc_value, _traceback) -> None:
        if exc_type is None:
            self.session.commit()
        else:
            self.session.rollback()
        if self._owned:
            self.session.close()


def get_uow() -> Generator[UnitOfWork, None, None]:
    """FastAPI dependency that closes each request transaction."""
    with UnitOfWork() as unit:
        yield unit

