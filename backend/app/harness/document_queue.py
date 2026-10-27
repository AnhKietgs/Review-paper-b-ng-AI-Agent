"""Bounded, restartable main document queue."""

from dataclasses import dataclass

from app.harness.memory import RunMemory


@dataclass(frozen=True)
class ChunkBatch:
    """One batch reserved until successfully processed."""

    chunk_ids: list[str]


class DocumentQueue:
    """Keep source coverage explicit in checkpoint memory."""

    def __init__(self, memory: RunMemory, batch_size: int = 2):
        self.memory = memory
        self.batch_size = batch_size

    def next_main_batch(self, run_id: str) -> ChunkBatch | None:
        """Reserve the next batch without marking it processed."""
        state = self.memory.load(run_id)
        if not state.current_batch_ids:
            state.current_batch_ids = state.remaining_chunk_ids[: self.batch_size]
            self.memory.save(state)
        return ChunkBatch(state.current_batch_ids) if state.current_batch_ids else None

    def mark_processed(self, run_id: str, chunk_ids: list[str]) -> None:
        """Acknowledge only the reserved batch and prevent duplicate coverage."""
        state = self.memory.load(run_id)
        if set(chunk_ids) != set(state.current_batch_ids):
            raise ValueError("Only the current batch may be acknowledged")
        for chunk_id in chunk_ids:
            if chunk_id not in state.processed_chunk_ids:
                state.processed_chunk_ids.append(chunk_id)
        state.remaining_chunk_ids = [
            item for item in state.remaining_chunk_ids if item not in chunk_ids
        ]
        state.current_batch_ids = []
        self.memory.save(state)

    def reference_scope(self, run_id: str) -> set[str]:
        """Return only manually selected related paper IDs."""
        return set(self.memory.load(run_id).scope.reference_versions)
