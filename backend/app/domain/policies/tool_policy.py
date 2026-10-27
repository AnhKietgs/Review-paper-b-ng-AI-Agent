"""Explicit per-role tool allowlists."""

TOOL_ALLOWLIST = {
    "supervisor": {"read_rubric"},
    "scientific_review": {"read_chunks"},
    "related_work": {"read_chunks", "search_reference"},
    "evidence_verifier": {"read_chunks"},
}
