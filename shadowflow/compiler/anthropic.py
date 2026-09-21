from __future__ import annotations

import json
import os
from typing import Any

import httpx

from shadowflow.compiler.base import WorkflowCompiler
from shadowflow.engine.risk import apply_risk_policy
from shadowflow.models import ShadowFailure, TraceBundle, WorkflowSpec


class AnthropicCompiler(WorkflowCompiler):
    name = "anthropic"

    def __init__(self) -> None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required for the anthropic compiler route")
        self.api_key = api_key
        self.model = os.getenv("SHADOWFLOW_ANTHROPIC_MODEL", "claude-sonnet-4-5")
        self.timeout = float(os.getenv("SHADOWFLOW_LLM_TIMEOUT_SECONDS", "60"))

    def compile(self, trace: TraceBundle) -> WorkflowSpec:
        data = self._chat_json(
            "Compile this browser trace into WorkflowSpec JSON.",
            {"trace": trace.model_dump(mode="json"), "workflow_schema": WorkflowSpec.model_json_schema()},
        )
        return apply_risk_policy(WorkflowSpec.model_validate(data))

    def repair(self, trace: TraceBundle, workflow: WorkflowSpec, failures: list[ShadowFailure]) -> WorkflowSpec:
        data = self._chat_json(
            "Repair the workflow from deterministic shadow failures. Keep human approval gates. Prefer accessibility semantics.",
            {
                "trace": trace.model_dump(mode="json"),
                "workflow": workflow.model_dump(mode="json"),
                "failures": [item.model_dump(mode="json") for item in failures],
                "workflow_schema": WorkflowSpec.model_json_schema(),
            },
        )
        return apply_risk_policy(WorkflowSpec.model_validate(data))

    def _chat_json(self, system: str, user: Any) -> dict[str, Any]:
        body = {
            "model": self.model,
            "max_tokens": 6000,
            "temperature": 0,
            "system": system + " Return JSON only.",
            "messages": [{"role": "user", "content": json.dumps(user, ensure_ascii=False)}],
        }
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post("https://api.anthropic.com/v1/messages", json=body, headers=headers)
            response.raise_for_status()
        data = response.json()
        text = next(block["text"] for block in data["content"] if block.get("type") == "text")
        return json.loads(text)
