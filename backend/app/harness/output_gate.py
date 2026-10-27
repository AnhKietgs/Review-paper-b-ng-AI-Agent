"""Deterministic validation independent of the model's confidence."""

from pydantic import BaseModel, Field, ValidationError

from app.agents.schemas import FindingDraft
from app.harness.state import RunScope


class ValidationResult(BaseModel):
    """Checks visible to users in the trace."""

    passed: bool
    checks: dict[str, bool] = Field(default_factory=dict)
    reason_codes: list[str] = Field(default_factory=list)
    repair_allowed: bool = False


def normalize_quote(text: str) -> str:
    """Ignore extraction whitespace while preserving words and case."""
    return " ".join(text.split())


class OutputGate:
    """Validate schema, source identity, exact quote and source locator."""

    def __init__(self, catalog):
        self.catalog = catalog

    def validate(
        self, finding: FindingDraft | dict, scope: RunScope
    ) -> ValidationResult:
        """A pass proves provenance, not scientific correctness."""
        try:
            draft = FindingDraft.model_validate(finding)
        except ValidationError:
            return ValidationResult(
                passed=False, checks={"schema": False}, reason_codes=["invalid_schema"]
            )
        checks = {
            "schema": True,
            "source": True,
            "quote": True,
            "locator": True,
            "comparison": True,
        }
        reasons = []
        if not draft.evidence:
            checks["source"] = False
            reasons.append("missing_evidence")
        for reference in draft.evidence:
            chunk = self.catalog.chunk(reference.chunk_id)
            if (
                chunk is None
                or chunk["paper_id"] != reference.paper_id
                or chunk["content_version"] != reference.content_version
                or not scope.permits(reference.paper_id, reference.content_version)
            ):
                checks["source"] = False
                reasons.append("source_version_mismatch")
                continue
            if not normalize_quote(reference.quote) or normalize_quote(
                reference.quote
            ) not in normalize_quote(chunk["text"]):
                checks["quote"] = False
                reasons.append("quote_not_found")
            locator = chunk.get("locator")
            if (
                not locator
                or locator["status"] != "resolved"
                or locator["type"] != reference.locator_type
                or locator["value"] != reference.locator_value
            ):
                checks["locator"] = False
                reasons.append("unresolved_or_wrong_locator")
        if draft.kind == "comparison":
            sources = {item.paper_id for item in draft.evidence}
            required = {scope.main_paper_id, *draft.compared_paper_ids}
            if (
                not draft.compared_paper_ids
                or not required <= sources
                or not set(draft.compared_paper_ids) <= set(scope.reference_versions)
            ):
                checks["comparison"] = False
                reasons.append("comparison_missing_source")
        passed = all(checks.values())
        return ValidationResult(
            passed=passed, checks=checks, reason_codes=list(dict.fromkeys(reasons))
        )
