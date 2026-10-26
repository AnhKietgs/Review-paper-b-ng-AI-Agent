"""Rubric persistence port."""

from typing import Protocol


class RubricRepository(Protocol):
    """Versioned rubric operations expected by application service."""

    def get(self, rubric_id: str): ...

    def list(self, limit: int, offset: int): ...

