"""Bounded provider retry, schema repair and sanitized failure."""

from types import SimpleNamespace

import httpx
import pytest
from groq import RateLimitError

from app.agents.ports import LLMFailure
from app.agents.schemas import AgentAction
from app.infrastructure.groq.client import GroqClient


def test_rate_limit_retries_are_bounded_and_safe():
    calls = []

    def completion(**_kwargs):
        calls.append(1)
        raise RateLimitError(
            "secret-token",
            response=httpx.Response(
                429, request=httpx.Request("POST", "https://example.invalid")
            ),
            body=None,
        )

    adapter = GroqClient(
        "secret-token",
        "configured-model",
        completion=completion,
        sleep=lambda _seconds: None,
    )
    with pytest.raises(LLMFailure, match="rate_limited") as error:
        adapter.generate_json([{"role": "user", "content": "JSON please"}], AgentAction)
    assert len(calls) == 3
    assert "secret-token" not in str(error.value)


def test_schema_gets_only_one_repair():
    responses = iter(
        ["{}", '{"action":"finish","reason":"Done","reference_paper_id":null}']
    )
    calls = []

    def completion(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=next(responses)))],
            usage=SimpleNamespace(total_tokens=10),
        )

    adapter = GroqClient("key", "model", completion=completion)
    assert (
        adapter.generate_json([{"role": "user", "content": "JSON"}], AgentAction).action
        == "finish"
    )
    assert len(calls) == 2
    assert calls[0]["response_format"] == {"type": "json_object"}
    assert adapter.usage["tokens"] == 20
