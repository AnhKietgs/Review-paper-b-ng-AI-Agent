"""Qualitative rubric version snapshots."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Criterion:
    """One prompt used to critique evidence."""

    code: str
    question: str
    guidance: str
    order_index: int
