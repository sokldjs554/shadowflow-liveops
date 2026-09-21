from __future__ import annotations

import json
import os
from typing import Any

import httpx

from shadowflow.compiler.base import WorkflowCompiler
from shadowflow.engine.risk import apply_risk_policy
from shadowflow.models import ShadowFailure, TraceBundle, WorkflowSpec


class OpenAICompatibleCompiler(WorkflowCompiler):
    name = "openai-compatible"

    def __init__(self) -> None:
        self.base_url = os.getenv("SHADOWFLOW_OPENAI_BASE_URL", "http://127.0.0.1:11434/v1").rstrip("/")
        self.model = os.getenv("SHADOWFLOW_OPENAI_MODEL", "qwen2.5-coder:7b")
        self.api_key = os.getenv("SHADOWFLOW_OPENAI_API_KEY", "ollama")
        self.timeout = float(os.getenv("SHADOWFLOW_LLM_TIMEOUT_SECONDS", "60"))

    def compile(self, trace: TraceBundle) -> WorkflowSpec:
        payload = self._chat_json(
            "You compile browser traces into typed workflow JSON. Preserve evidence provenance. "
            "Do not invent credentials, URLs, or external side effects. Return only JSON matching WorkflowSpec.",
            {
                "trace": trace.model_dump(mode="json"),
                "workflow_schema": WorkflowSpec.model_json_schema(),
            },
        )
        return apply_risk_policy(WorkflowSpec.model_validate(payload))

    def repair(self, trace: TraceBundle, workflow: WorkflowSpec, failures: list[ShadowFailure]) -> WorkflowSpec:
        payload = self._chat_json(
            "Repair a workflow after deterministic shadow failures. Prefer role/name or label locators over CSS selectors. "
            "Never remove approval requirements or validation steps. Return only JSON matching WorkflowSpec.",
            {
                "trace": trace.model_dump(mode="json"),
                "workflow": workflow.model_dump(mode="json"),
                "failures": [item.model_dump(mode="json") for item in failures],
                "workflow_schema": WorkflowSpec.model_json_schema(),
            },
        )
        return apply_risk_policy(WorkflowSpec.model_validate(payload))

    def _chat_json(self, system: str, user: Any) -> dict[str, Any]:
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(f"{self.base_url}/chat/completions", json=body, headers=headers)
            response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
