"""Public runtime smoke tests."""

from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok():
    response = TestClient(app).get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_runtime_exposes_mode_only(monkeypatch):
    monkeypatch.setenv("DEMO_LLM_MODE", "fixture")
    monkeypatch.setenv("GROQ_API_KEY", "do-not-expose")
    response = TestClient(app).get("/api/v1/runtime")
    assert response.status_code == 200
    assert response.json() == {"llm_mode": "fixture"}
    assert "do-not-expose" not in response.text
