"""Run lifecycle request and response contracts."""

from typing import Literal

from pydantic import BaseModel


class RunRequest(BaseModel):
    """Full review or verification of edits, always on a new revision."""

    mode: Literal["review", "verify"] = "review"


class RunAccepted(BaseModel):
    """Accepted background execution and its fresh draft revision."""

    run_id: str
    review_id: str
    status: str
