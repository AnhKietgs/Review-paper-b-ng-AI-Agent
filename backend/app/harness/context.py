"""Explicit context assembly from approved tool results."""

from app.harness.state import RunState


class ContextBuilder:
    """Build only the context needed for the selected role."""

    def build(self, state: RunState, chunks: list[dict], criteria: list[dict]) -> dict:
        """Provide bounded source content and public progress metadata."""
        return {
            "scope": state.scope.model_dump(),
            "progress": {
                "remaining": len(state.remaining_chunk_ids),
                "processed": len(state.processed_chunk_ids),
                "batch_count": state.batch_count,
                "turn_count": state.turn_count,
            },
            "chunks": chunks,
            "criteria": criteria,
            "pending_findings": state.pending_findings,
            "reference_assessments": state.reference_assessments,
        }
