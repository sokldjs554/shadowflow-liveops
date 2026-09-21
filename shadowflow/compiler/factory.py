from __future__ import annotations

from shadowflow.compiler.anthropic import AnthropicCompiler
from shadowflow.compiler.base import WorkflowCompiler
from shadowflow.compiler.deterministic import DeterministicDemoCompiler
from shadowflow.compiler.openai_compat import OpenAICompatibleCompiler


def build_compiler(name: str) -> WorkflowCompiler:
    if name == "deterministic-demo":
        return DeterministicDemoCompiler()
    if name in {"openai-compatible", "ollama"}:
        return OpenAICompatibleCompiler()
    if name == "anthropic":
        return AnthropicCompiler()
    raise ValueError(f"Unsupported compiler provider: {name}")
