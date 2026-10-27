"""Review persistence contract."""

from typing import Protocol


class ReviewRepository(Protocol):
    """Operations required by ReviewService."""

    def get(self, review_id: str):
        """Get records through the persistence adapter."""
        ...

    def list(self, limit: int, offset: int):
        """List records through the persistence adapter."""
        ...
