from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Literal

from shadowflow.compiler.factory import build_compiler
from shadowflow.engine.codegen import generate_playwright
from shadowflow.engine.evidence import build_evidence
from shadowflow.engine.risk import classify_workflow
from shadowflow.engine.shadow import execute_shadow
from shadowflow.engine.trace import normalize_bundle
from shadowflow.models import Attempt, MergePacket, RunStage, TraceBundle
from shadowflow.store import RunStore


class ShadowFlowPipeline:
    def __init__(self, project_root: Path, store: RunStore) -> None:
        self.project_root = project_root
        self.store = store

    def start(self, provider: str) -> str:
        run_id = uuid.uuid4().hex[:12]
        self.store.create(run_id, provider)
        return run_id

    def execute(self, run_id: str, trace: TraceBundle) -> MergePacket:
        record = self.store.get(run_id)
        compiler = build_compiler(record.provider)
        started = time.perf_counter()
        try:
            self._event(run_id, RunStage.NORMALIZING, "Normalizing recorded actions and redacting sensitive inputs")
            normalized = normalize_bundle(trace)

            self._event(run_id, RunStage.COMPILING, "Compiling low-level browser actions into a typed workflow")
            workflow_v1 = compiler.compile(normalized)

            self._event(run_id, RunStage.SHADOWING, "Executing baseline and drifted digital-twin variants")
            attempt1 = self._attempt(1, "Initial trace compilation", workflow_v1)
            attempts = [attempt1]

            failures = [failure for run in attempt1.shadow_runs for failure in run.failures]
            if failures:
                self._event(
                    run_id,
                    RunStage.REPAIRING,
                    "Shadow drift rejected brittle targets; repairing from recorded accessibility evidence",
                )
                workflow_v2 = compiler.repair(normalized, workflow_v1, failures)
                self._event(run_id, RunStage.SHADOWING, "Re-running the same shadow variants after repair")
                attempt2 = self._attempt(2, "Promote selectors to semantic accessibility locators", workflow_v2)
                attempts.append(attempt2)

            final = attempts[-1]
            all_shadow_pass = final.passed_variants == final.total_variants
            risks = classify_workflow(final.workflow)
            publish_requires_approval = any(item.approval_required for item in risks)

            self._event(run_id, RunStage.GENERATING, "Generating Playwright code from the verified typed workflow")
            generated = generate_playwright(final.workflow)
            evidence = build_evidence(normalized, attempts, risks)
            verdict: Literal["ready_with_approval", "approved_for_export", "blocked"] = (
                "ready_with_approval" if all_shadow_pass and publish_requires_approval else "blocked"
            )
            packet = MergePacket(
                run_id=run_id,
                verdict=verdict,
                trace=normalized,
                attempts=attempts,
                risks=risks,
                generated=generated,
                evidence=evidence,
                limitations=[
                    "The default compiler is deterministic and exists to reproduce the pipeline; it is not an LLM-quality benchmark.",
                    "The live-ops workspace and browser traces are synthetic and do not represent GameSpring's private tools or internal process.",
                    "Shadow execution uses a typed synthetic digital twin; it does not perform real player-visible publishing.",
                    "Open-model and hosted LLM adapters are integrated behind the same schema but require the user's own endpoint/credential for real inference.",
                ],
                metrics={
                    "trace_events": len(normalized.events),
                    "workflow_steps": len(final.workflow.steps),
                    "attempts": len(attempts),
                    "shadow_variants": final.total_variants,
                    "shadow_passed": final.passed_variants,
                    "approval_gates": sum(item.approval_required for item in risks),
                    "pipeline_ms": int((time.perf_counter() - started) * 1000),
                },
            )
            self.store.update(
                run_id,
                stage=RunStage.COMPLETE,
                status_message="Ready with approval boundary" if verdict == "ready_with_approval" else "Blocked",
                packet=packet,
                event={"stage": "complete", "message": f"Verdict: {verdict}"},
            )
            return packet
        except Exception as exc:
            self.store.update(
                run_id,
                stage=RunStage.FAILED,
                status_message=f"Failed: {exc}",
                event={"stage": "failed", "message": str(exc)},
            )
            raise

    def approve(self, run_id: str, *, actor: str, reason: str) -> MergePacket:
        record = self.store.get(run_id)
        if record.packet is None:
            raise ValueError("Run has no merge packet")
        if record.packet.verdict != "ready_with_approval":
            raise ValueError(f"Run is not awaiting approval: {record.packet.verdict}")
        packet = record.packet.model_copy(update={"verdict": "approved_for_export"})
        approval = {
            "actor": actor,
            "reason": reason,
            "scope": "generated automation export only; no real publish executed",
        }
        self.store.update(
            run_id,
            status_message="Approved for generated-code export",
            packet=packet,
            approval=approval,
            event={"stage": "approval", "message": f"Approved for export by {actor}"},
        )
        return packet

    def _attempt(self, number: int, summary: str, workflow: object) -> Attempt:
        # WorkflowSpec type is enforced by compiler return contract; keeping this method narrow helps tests inject nothing else.
        from shadowflow.models import WorkflowSpec

        if not isinstance(workflow, WorkflowSpec):
            raise TypeError("workflow must be WorkflowSpec")
        variants = ["baseline", "selector-drift-1", "selector-drift-2", "selector-drift-3"]
        shadow_runs = [execute_shadow(workflow, variant=variant, simulate_approval=True) for variant in variants]
        passed = sum(run.status == "pass" for run in shadow_runs)
        return Attempt(
            number=number,
            summary=summary,
            workflow=workflow,
            shadow_runs=shadow_runs,
            passed_variants=passed,
            total_variants=len(shadow_runs),
        )

    def _event(self, run_id: str, stage: RunStage, message: str) -> None:
        self.store.update(
            run_id,
            stage=stage,
            status_message=message,
            event={"stage": stage.value, "message": message},
        )
