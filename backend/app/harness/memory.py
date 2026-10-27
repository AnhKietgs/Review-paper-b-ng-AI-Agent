"""JSON checkpoint memory with optional durable SQL storage."""

from sqlalchemy.orm import Session

from app.harness.state import RunState
from app.infrastructure.persistence.orm_models import RunCheckpointRow


class RunMemory:
    """Persist a copied state after each completed harness turn."""

    def __init__(self, session: Session | None = None):
        self.session = session
        self._states: dict[str, dict] = {}

    def save(self, state: RunState) -> None:
        """Replace a checkpoint as part of the caller's transaction."""
        data = state.model_dump(mode="json")
        if self.session is None:
            self._states[state.run_id] = data
            return
        row = self.session.get(RunCheckpointRow, state.run_id)
        if row is None:
            self.session.add(RunCheckpointRow(run_id=state.run_id, state_json=data))
        else:
            row.state_json = data
        self.session.flush()

    def load(self, run_id: str) -> RunState:
        """Restore isolated state from the last committed turn."""
        if self.session is None:
            return RunState.model_validate(self._states[run_id])
        row = self.session.get(RunCheckpointRow, run_id)
        if row is None:
            raise KeyError(run_id)
        return RunState.model_validate(row.state_json)
