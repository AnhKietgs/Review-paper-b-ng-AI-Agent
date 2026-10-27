"""Safe, ordered trace and explicit context boundary."""

from app.harness.context import ContextBuilder
from app.harness.events import RunEventInput, RunEventRecorder
from app.harness.state import RunScope, RunState


def test_events_monotonic_and_context_has_no_secrets(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "sensitive-key")
    events = RunEventRecorder()
    for action in ("run_started", "context_built", "checkpoint_saved"):
        events.append("r", RunEventInput(agent="harness", action=action))
    assert [event["sequence"] for event in events.items] == [1, 2, 3]
    state = RunState(
        run_id="r",
        review_id="v",
        scope=RunScope(
            main_paper_id="p",
            main_version=1,
            rubric_id="q",
            rubric_version=1,
        ),
    )
    context = ContextBuilder().build(state, [], [])
    assert "sensitive-key" not in str(context)
    assert "scope" in context and "progress" in context
