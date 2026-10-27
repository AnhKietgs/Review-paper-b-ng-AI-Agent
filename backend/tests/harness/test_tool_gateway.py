"""Permission enforcement precedes tool dispatch."""

from app.harness.events import RunEventRecorder
from app.harness.state import RunScope
from app.harness.tool_gateway import ToolCall, ToolGateway


class Catalog:
    def is_active(self, paper_id):
        return paper_id != "deleted"

    def chunk(self, chunk_id):
        return {"id": chunk_id, "paper_id": "outside", "content_version": 1}

    def chunks(self, paper_id, version):
        raise AssertionError("denied request reached handler")


def test_outside_scope_and_unknown_tool_denied_before_dispatch():
    events = RunEventRecorder()
    gateway = ToolGateway(Catalog(), events, "run")
    scope = RunScope(
        main_paper_id="main",
        main_version=1,
        reference_versions={"ref": 1},
        rubric_id="r",
        rubric_version=1,
    )
    assert not gateway.execute(
        ToolCall(
            agent="related_work",
            name="search_reference",
            arguments={"paper_id": "outside"},
        ),
        scope,
    ).allowed
    assert not gateway.execute(
        ToolCall(agent="scientific_review", name="shell", arguments={}), scope
    ).allowed
    assert not gateway.execute(
        ToolCall(
            agent="evidence_verifier",
            name="read_chunks",
            arguments={"chunk_ids": ["bad"]},
        ),
        scope,
    ).allowed
    assert [event["permission_result"] for event in events.items] == ["deny"] * 3


def test_gateway_cannot_read_main_paper_as_comparison_reference():
    events = RunEventRecorder()
    gateway = ToolGateway(Catalog(), events, "run")
    scope = RunScope(
        main_paper_id="main",
        main_version=1,
        reference_versions={"main": 1},
        rubric_id="r",
        rubric_version=1,
    )
    result = gateway.execute(
        ToolCall(
            agent="related_work",
            name="search_reference",
            arguments={"paper_id": "main"},
        ),
        scope,
    )
    assert not result.allowed
    assert result.reason == "reference_not_selected_or_deleted"
    assert events.items[-1]["permission_result"] == "deny"
