from __future__ import annotations

import json
from typing import Any

from shadowflow.compiler import openai_compat
from shadowflow.engine.trace import synthetic_liveops_trace


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self.payload


class FakeClient:
    def __init__(self, payload: dict[str, Any], calls: list[dict[str, Any]]) -> None:
        self.payload = payload
        self.calls = calls

    def __enter__(self) -> FakeClient:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def post(self, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"url": url, **kwargs})
        return FakeResponse(self.payload)


def test_openai_compatible_route_requests_structured_json(monkeypatch: Any) -> None:
    compiler = openai_compat.OpenAICompatibleCompiler()
    calls: list[dict[str, Any]] = []
    expected = {"hello": "workflow"}
    payload = {"choices": [{"message": {"content": json.dumps(expected)}}]}
    monkeypatch.setattr(openai_compat.httpx, "Client", lambda timeout: FakeClient(payload, calls))

    result = compiler._chat_json("system", synthetic_liveops_trace().model_dump(mode="json"))

    assert result == expected
    assert calls[0]["url"].endswith("/chat/completions")
    assert calls[0]["json"]["response_format"] == {"type": "json_object"}
    assert calls[0]["json"]["model"] == compiler.model
