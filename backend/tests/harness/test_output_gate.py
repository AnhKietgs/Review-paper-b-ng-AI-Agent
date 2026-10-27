"""Evidence identity, locator and comparison coverage gates."""

from copy import deepcopy

from app.domain.policies.approval import ApprovalPolicy
from app.harness.output_gate import OutputGate
from app.harness.state import RunScope


class Catalog:
    def chunk(self, chunk_id):
        paper_id = "ref" if chunk_id == "ref-chunk" else "main"
        return {
            "id": chunk_id,
            "paper_id": paper_id,
            "content_version": 1,
            "text": "The sample contains 24 participants.",
            "locator": {"type": "pdf_page", "value": "2", "status": "resolved"},
        }


def evidence(paper="main", chunk="main-chunk"):
    return {
        "paper_id": paper,
        "content_version": 1,
        "chunk_id": chunk,
        "quote": "24 participants",
        "locator_type": "pdf_page",
        "locator_value": "2",
    }


def test_gate_checks_exact_version_quote_locator_and_comparison():
    scope = RunScope(
        main_paper_id="main",
        main_version=1,
        reference_versions={"ref": 1},
        rubric_id="r",
        rubric_version=1,
    )
    gate = OutputGate(Catalog())
    finding = {
        "id": "finding",
        "claim": "The study has a small sample.",
        "criterion_code": "method",
        "kind": "limitation",
        "evidence": [evidence()],
    }
    assert gate.validate(finding, scope).passed
    wrong_version = deepcopy(finding)
    wrong_version["evidence"][0]["content_version"] = 2
    assert "source_version_mismatch" in gate.validate(wrong_version, scope).reason_codes
    wrong_quote = deepcopy(finding)
    wrong_quote["evidence"][0]["quote"] = "100 participants"
    assert not gate.validate(wrong_quote, scope).passed
    blank_quote = deepcopy(finding)
    blank_quote["evidence"][0]["quote"] = "   "
    assert not gate.validate(blank_quote, scope).passed
    comparison = {**finding, "kind": "comparison", "compared_paper_ids": ["ref"]}
    assert "comparison_missing_source" in gate.validate(comparison, scope).reason_codes
    comparison["evidence"] = [evidence(), evidence("ref", "ref-chunk")]
    assert gate.validate(comparison, scope).passed
    assert not gate.validate({"claim": 7}, scope).passed


def test_unresolved_locator_and_approval_labels():
    catalog = Catalog()
    original = catalog.chunk
    catalog.chunk = lambda chunk_id: {
        **original(chunk_id),
        "locator": {"type": "pdf_page", "value": "2", "status": "unresolved_locator"},
    }
    scope = RunScope(
        main_paper_id="main", main_version=1, rubric_id="r", rubric_version=1
    )
    finding = {
        "id": "f",
        "claim": "Sample reported",
        "criterion_code": "method",
        "kind": "analysis",
        "evidence": [evidence()],
    }
    assert not OutputGate(catalog).validate(finding, scope).passed
    assert not ApprovalPolicy.can_approve([{"id": "f", "status": "unsupported"}], {"f"})
    human = [{"id": "f", "status": "needs_human_review"}]
    assert not ApprovalPolicy.can_approve(human)
    assert ApprovalPolicy.can_approve(human, {"f"})
    assert human[0]["status"] == "needs_human_review"
