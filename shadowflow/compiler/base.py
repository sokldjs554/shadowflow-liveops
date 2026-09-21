from __future__ import annotations

from abc import ABC, abstractmethod

from shadowflow.models import ShadowFailure, TraceBundle, WorkflowSpec


class WorkflowCompiler(ABC):
    name: str

    @abstractmethod
    def compile(self, trace: TraceBundle) -> WorkflowSpec:
        raise NotImplementedError

    @abstractmethod
    def repair(
        self,
        trace: TraceBundle,
        workflow: WorkflowSpec,
        failures: list[ShadowFailure],
    ) -> WorkflowSpec:
        raise NotImplementedError
