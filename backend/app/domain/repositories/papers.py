"""Paper persistence port."""

from typing import Protocol

from typing import Any

PaperRow = Any


class PaperRepository(Protocol):
    """Operations needed by PaperService."""

    def add(self, paper: PaperRow) -> None:
        """Add records through the persistence adapter."""
        ...

    def get(self, paper_id: str) -> PaperRow | None:
        """Get records through the persistence adapter."""
        ...

    def list(self, limit: int, offset: int) -> tuple[list[PaperRow], int]:
        """List records through the persistence adapter."""
        ...
