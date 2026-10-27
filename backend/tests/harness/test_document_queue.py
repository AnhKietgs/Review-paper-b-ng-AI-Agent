"""Document coverage and checkpoint invariants."""

from app.harness.document_queue import DocumentQueue
from app.harness.memory import RunMemory
from app.harness.state import RunScope, RunState


def test_main_chunks_once_and_checkpoint_reload():
    memory = RunMemory()
    state = RunState(
        run_id="run",
        review_id="review",
        scope=RunScope(
            main_paper_id="main",
            main_version=1,
            reference_versions={"ref": 2},
            rubric_id="rubric",
            rubric_version=1,
        ),
        remaining_chunk_ids=["a", "b", "c"],
    )
    memory.save(state)
    queue = DocumentQueue(memory, batch_size=2)
    assert queue.next_main_batch("run").chunk_ids == ["a", "b"]
    queue.mark_processed("run", ["a", "b"])
    assert queue.next_main_batch("run").chunk_ids == ["c"]
    queue.mark_processed("run", ["c"])
    assert queue.next_main_batch("run") is None
    restored = memory.load("run")
    assert restored.processed_chunk_ids == ["a", "b", "c"]
    assert restored.remaining_chunk_ids == []
    assert queue.reference_scope("run") == {"ref"}
