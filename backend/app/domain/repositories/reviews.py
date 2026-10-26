"""Review persistence contract."""

from typing import Protocol


class ReviewRepository(Protocol):
    """Operations required by ReviewService."""

    def get(self, review_id: str): ...

    def list(self, limit: int, offset: int): ...

