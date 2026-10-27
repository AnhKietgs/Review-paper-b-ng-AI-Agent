"""Run state names exposed through REST."""

from enum import StrEnum


class RunStatus(StrEnum):
    """Durable execution lifecycle."""

    QUEUED = "queued"
    RUNNING = "running"
    INTERRUPTED = "interrupted"
    COMPLETED = "completed"
    INCOMPLETE = "incomplete"
    FAILED = "failed"
