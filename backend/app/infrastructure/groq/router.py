"""Route each harness agent to its configured Groq model."""

from app.infrastructure.groq.client import GroqClient


class GroqRouter:
    """Select a model client by logical agent role and aggregate usage."""

    def __init__(self, clients: dict[str, GroqClient]):
        self._clients = clients

    def for_role(self, role: str) -> GroqClient:
        """Return the configured model client for a harness role."""
        return self._clients[role]

    def model_for(self, role: str) -> str:
        """Return a role's model ID for safe run-trace display."""
        return self._clients[role].model

    @property
    def usage(self) -> dict[str, int]:
        """Aggregate token and request counts across configured clients."""
        return {
            key: sum(client.usage.get(key, 0) for client in self._clients.values())
            for key in ("calls", "tokens")
        }
