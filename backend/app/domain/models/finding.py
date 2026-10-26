"""Finding support states."""

from enum import StrEnum


class FindingStatus(StrEnum):
    """Evidence review state of one claim."""

    PENDING = "pending"
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    NEEDS_HUMAN_REVIEW = "needs_human_review"

