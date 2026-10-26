"""Paper persistence port."""

from typing import Protocol

from app.infrastructure.persistence.orm_models import PaperRow


class PaperRepository(Protocol):
    """Operations needed by PaperService."""

    def add(self, paper: PaperRow) -> None: ...

    def get(self, paper_id: str) -> PaperRow | None: ...

    def list(self, limit: int, offset: int) -> tuple[list[PaperRow], int]: ...

