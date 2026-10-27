"""On-demand workers, guarded routing and bounded document loop."""

from app.harness.events import RunEventRecorder
from app.harness.memory import RunMemory
from app.harness.runner import AgentRunner
from app.harness.state import RunScope, RunState
from app.infrastructure.groq.fixture_client import FixtureClient


class Catalog:
    def is_active(self, _paper_id):
        return True

    def chunk(self, chunk_id):
        paper_id = "ref" if chunk_id.startswith("ref") else "main"
        return {
            "id": chunk_id,
            "paper_id": paper_id,
            "content_version": 1,
            "text": "The sample contains 24 participants.",
            "locator": {"type": "pdf_page", "value": "1", "status": "resolved"},
        }

    def chunks(self, paper_id, _version):
        return [self.chunk(f"{paper_id}-1")]

    def criteria(self, _rubric_id, _version):
        return [{"code": "method", "question": "Assess sample", "guidance": ""}]


def run_state(references=None, chunks=None, **limits):
    return RunState(
        run_id="run",
        review_id="review",
        scope=RunScope(
            main_paper_id="main",
            main_version=1,
            reference_versions=references or {},
            rubric_id="rubric",
            rubric_version=1,
        ),
        remaining_chunk_ids=chunks or ["main-1"],
        **limits,
    )


def execute(state, client=None):
    memory, events = RunMemory(), RunEventRecorder()
    runner = AgentRunner(client or FixtureClient(), Catalog(), memory, events)
    memory.save(state)
    while state.status == "running":
        state = runner.run_turn(state)
    return state, events


def test_no_reference_skips_comparator_and_calls_one_worker_per_turn():
    state, events = execute(run_state())
    assert state.status == "completed"
    assert state.call_counts.get("related_work", 0) == 0
    assert state.call_counts["scientific_review"] == 1
    assert state.call_counts["evidence_verifier"] == 1
    workers = [
        item
        for item in events.items
        if item["action"] == "agent_started" and item["agent"] != "supervisor"
    ]
    turns = [item["payload"]["turn"] for item in workers]
    assert len(turns) == len(set(turns))
    assert all(item["status"] == "supported" for item in state.findings)


def test_selected_reference_has_two_sided_evidence():
    state, _ = execute(run_state({"ref": 1}))
    assert state.status == "completed"
    assert state.reference_assessments["ref"]["status"] == "assessed"
    comparisons = [item for item in state.findings if item["kind"] == "comparison"]
    assert comparisons
    assert {source["paper_id"] for source in comparisons[0]["evidence"]} == {
        "main",
        "ref",
    }


def test_invalid_supervisor_action_does_not_call_worker_and_hits_budget():
    state, events = execute(
        run_state(max_turns=3), FixtureClient(force_action="compare")
    )
    assert state.status == "incomplete"
    assert state.call_counts.get("related_work", 0) == 0
    assert state.call_counts.get("evidence_verifier", 0) == 0
    assert any(item["action"] == "agent_skipped" for item in events.items)


def test_document_batch_budget_preserves_unprocessed_ids():
    state, _ = execute(run_state(chunks=[f"main-{i}" for i in range(5)], max_batches=1))
    assert state.status == "incomplete"
    assert len(state.processed_chunk_ids) == 2
    assert len(state.remaining_chunk_ids) == 3


def test_model_cannot_choose_persisted_finding_ids():
    import json
    from app.agents.schemas import ScientificOutput

    class ReusedIds(FixtureClient):
        def generate_json(self, messages, schema):
            result = super().generate_json(messages, schema)
            if schema is ScientificOutput:
                for item in result.findings:
                    item.id = "existing-foreign-finding"
            return result

    state, _ = execute(run_state(chunks=["main-1", "main-2"]), ReusedIds())
    assert len({f["id"] for f in state.findings}) == 2
    assert all(f["id"] != "existing-foreign-finding" for f in state.findings)
