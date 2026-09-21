from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ActionKind(StrEnum):
    NAVIGATE = "navigate"
    INPUT = "input"
    SELECT = "select"
    UPLOAD = "upload"
    CLICK = "click"
    PREVIEW = "preview"
    PUBLISH = "publish"


class SideEffect(StrEnum):
    NONE = "none"
    READ = "read"
    INTERNAL_WRITE = "internal_write"
    EXTERNAL_WRITE = "external_write"
    IRREVERSIBLE = "irreversible"


class TargetSnapshot(BaseModel):
    selector: str | None = None
    role: str | None = None
    accessible_name: str | None = None
    label: str | None = None
    text: str | None = None
    test_id: str | None = None


class TraceEvent(BaseModel):
    id: str
    seq: int = Field(ge=0)
    at: datetime
    page: str
    action: ActionKind
    target: TargetSnapshot | None = None
    value: Any = None
    before_hash: str | None = None
    after_hash: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TraceBundle(BaseModel):
    id: str
    title: str
    source: Literal["recorded", "synthetic-demo"]
    events: list[TraceEvent]
    redactions: list[str] = Field(default_factory=list)


class SemanticLocator(BaseModel):
    strategy: Literal["selector", "role_name", "label", "text"]
    selector: str | None = None
    role: str | None = None
    name: str | None = None
    label: str | None = None
    text: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class WorkflowStep(BaseModel):
    id: str
    intent: str
    action: ActionKind
    locator: SemanticLocator | None = None
    value: Any = None
    depends_on: list[str] = Field(default_factory=list)
    preconditions: list[str] = Field(default_factory=list)
    postconditions: list[str] = Field(default_factory=list)
    side_effect: SideEffect = SideEffect.NONE
    approval_required: bool = False
    source_event_ids: list[str] = Field(default_factory=list)


class WorkflowSpec(BaseModel):
    id: str
    title: str
    purpose: str
    version: int = 1
    compiler_route: str
    steps: list[WorkflowStep]
    warnings: list[str] = Field(default_factory=list)


class ShadowFailure(BaseModel):
    code: str
    step_id: str | None = None
    message: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class StepExecution(BaseModel):
    step_id: str
    status: Literal["pass", "fail", "approval_required", "skipped"]
    detail: str
    resolved_target: str | None = None


class ShadowRun(BaseModel):
    variant: str
    workflow_version: int
    status: Literal["pass", "fail", "approval_required"]
    steps: list[StepExecution]
    failures: list[ShadowFailure] = Field(default_factory=list)
    state_digest: str


class Attempt(BaseModel):
    number: int
    summary: str
    workflow: WorkflowSpec
    shadow_runs: list[ShadowRun]
    passed_variants: int
    total_variants: int


class RiskDecision(BaseModel):
    step_id: str
    side_effect: SideEffect
    approval_required: bool
    reason: str


class GeneratedArtifact(BaseModel):
    name: str
    language: str
    content: str
    sha256: str


class EvidenceRow(BaseModel):
    claim: str
    status: Literal["proven", "blocked", "needs_approval"]
    evidence: list[str]


class MergePacket(BaseModel):
    run_id: str
    verdict: Literal["ready_with_approval", "approved_for_export", "blocked"]
    trace: TraceBundle
    attempts: list[Attempt]
    risks: list[RiskDecision]
    generated: GeneratedArtifact
    evidence: list[EvidenceRow]
    limitations: list[str]
    metrics: dict[str, Any]


class RunStage(StrEnum):
    QUEUED = "queued"
    NORMALIZING = "normalizing"
    COMPILING = "compiling"
    SHADOWING = "shadowing"
    REPAIRING = "repairing"
    GENERATING = "generating"
    COMPLETE = "complete"
    FAILED = "failed"


class RunRecord(BaseModel):
    id: str
    stage: RunStage
    status_message: str
    provider: str
    created_at: str
    updated_at: str
    packet: MergePacket | None = None
    events: list[dict[str, Any]] = Field(default_factory=list)
    approval: dict[str, Any] | None = None
