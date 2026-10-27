"""The only dispatch path to document tools."""

from pydantic import BaseModel, Field

from app.domain.policies.tool_policy import TOOL_ALLOWLIST
from app.harness.events import RunEventInput, RunEventRecorder
from app.harness.state import RunScope


class ToolCall(BaseModel):
    """A tool invocation checked before its handler runs."""

    agent: str
    name: str
    arguments: dict = Field(default_factory=dict)


class ToolResult(BaseModel):
    """Safe tool outcome."""

    allowed: bool
    data: list[dict] = Field(default_factory=list)
    reason: str = ""


class ToolGateway:
    """Enforce role, paper and content-version permission before reads."""

    def __init__(self, catalog, events: RunEventRecorder, run_id: str):
        self.catalog = catalog
        self.events = events
        self.run_id = run_id

    def _record(
        self, call: ToolCall, allowed: bool, reason: str, source_ids: list[str]
    ) -> None:
        self.events.append(
            self.run_id,
            RunEventInput(
                agent=call.agent,
                action="tool_result" if allowed else "permission_denied",
                tool=call.name,
                permission_result="allow" if allowed else "deny",
                output_summary=reason,
                payload={"source_ids": source_ids},
            ),
        )

    def execute(self, call: ToolCall, scope: RunScope) -> ToolResult:
        """Check permission then dispatch one allowlisted tool."""
        data: list[dict] = []
        reason = "allowed"
        if call.name not in TOOL_ALLOWLIST.get(call.agent, set()):
            reason = "tool_not_allowed"
        elif call.name == "read_chunks":
            for chunk_id in call.arguments.get("chunk_ids", []):
                chunk = self.catalog.chunk(chunk_id)
                if (
                    chunk is None
                    or not scope.permits(chunk["paper_id"], chunk["content_version"])
                    or not self.catalog.is_active(chunk["paper_id"])
                    or (
                        call.agent == "scientific_review"
                        and chunk["paper_id"] != scope.main_paper_id
                    )
                ):
                    reason = "source_outside_scope"
                    data = []
                    break
                data.append(chunk)
        elif call.name == "search_reference":
            paper_id = call.arguments.get("paper_id", "")
            if (
                paper_id == scope.main_paper_id
                or paper_id not in scope.reference_versions
                or not self.catalog.is_active(paper_id)
            ):
                reason = "reference_not_selected_or_deleted"
            else:
                chunks = self.catalog.chunks(
                    paper_id, scope.reference_versions[paper_id]
                )
                words = set(str(call.arguments.get("query", "")).lower().split())
                data = sorted(
                    chunks,
                    key=lambda item: len(
                        words.intersection(item["text"].lower().split())
                    ),
                    reverse=True,
                )[:2]
        elif call.name == "read_rubric":
            data = self.catalog.criteria(scope.rubric_id, scope.rubric_version)
        allowed = reason == "allowed"
        self._record(
            call, allowed, reason, [item["id"] for item in data if "id" in item]
        )
        return ToolResult(allowed=allowed, data=data, reason=reason)
