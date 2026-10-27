"""Rubric persistence port."""

from typing import Protocol


class RubricRepository(Protocol):
    """Versioned rubric operations expected by application service."""

    def get(self, rubric_id: str):
        """Get records through the persistence adapter."""
        ...

    def list(self, limit: int, offset: int):
        """List records through the persistence adapter."""
        ...
