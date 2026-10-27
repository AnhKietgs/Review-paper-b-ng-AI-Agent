"""Run persistence contract."""

from typing import Protocol


class RunRepository(Protocol):
    """Lookup and public event operations."""

    def get(self, run_id: str):
        """Get records through the persistence adapter."""
        ...

    def events(self, run_id: str, after: int):
        """Events records through the persistence adapter."""
        ...
