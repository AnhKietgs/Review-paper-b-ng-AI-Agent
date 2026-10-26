"""Review revision states."""

from enum import StrEnum


class ReviewStatus(StrEnum):
    """Human controlled review lifecycle."""

    DRAFT = "draft"
    APPROVED = "approved"

