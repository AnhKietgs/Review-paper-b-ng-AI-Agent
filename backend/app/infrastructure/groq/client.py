"""Groq JSON adapter with explicit retry and schema validation budgets."""

import json
import time

from groq import APIError, Groq, RateLimitError
from pydantic import ValidationError

from app.agents.ports import LLMFailure


class GroqClient:
    """Call configured Groq model without exposing credentials in failures."""

    def __init__(
        self, api_key: str, model: str, completion=None, sleep=time.sleep, on_retry=None
    ):
        self.model = model
        self._completion = (
            completion
            or Groq(
                api_key=api_key,
                max_retries=0,
                timeout=30,
            ).chat.completions.create
        )
        self._sleep = sleep
        self._on_retry = on_retry
        self.usage = {"calls": 0, "tokens": 0}

    def _request(self, messages):
        for attempt in range(3):
            try:
                self.usage["calls"] += 1
                response = self._completion(
                    model=self.model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0,
                    max_completion_tokens=4096,
                )
                self.usage["tokens"] += getattr(response.usage, "total_tokens", 0) or 0
                return response.choices[0].message.content
            except RateLimitError as exc:
                if attempt == 2:
                    raise LLMFailure("rate_limited") from exc
                if self._on_retry:
                    self._on_retry(attempt + 1)
                self._sleep(min(2**attempt, 4))
            except APIError as exc:
                raise LLMFailure("provider_unavailable") from exc
        raise LLMFailure("provider_unavailable")

    def generate_json(self, messages, schema):
        """Parse structured output and allow one schema-only repair attempt."""
        request = list(messages) + [
            {
                "role": "system",
                "content": "Return only JSON matching this schema: "
                + json.dumps(schema.model_json_schema(), ensure_ascii=False),
            }
        ]
        for attempt in range(2):
            content = self._request(request)
            try:
                return schema.model_validate_json(content or "")
            except ValidationError as exc:
                if attempt:
                    raise LLMFailure("invalid_model_output") from exc
                request.append(
                    {
                        "role": "user",
                        "content": "Previous output failed the JSON schema. "
                        "Return a valid object, preserving source IDs and exact quotes "
                        "from the original context.",
                    }
                )
        raise LLMFailure("invalid_model_output")
