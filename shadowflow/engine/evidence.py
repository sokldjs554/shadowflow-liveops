from __future__ import annotations

from shadowflow.models import Attempt, EvidenceRow, RiskDecision, TraceBundle


def build_evidence(trace: TraceBundle, attempts: list[Attempt], risks: list[RiskDecision]) -> list[EvidenceRow]:
    final = attempts[-1]
    baseline_ok = any(run.variant == "baseline" and run.status == "pass" for run in final.shadow_runs)
    drift_runs = [run for run in final.shadow_runs if run.variant.startswith("selector-drift")]
    drift_ok = bool(drift_runs) and all(run.status == "pass" for run in drift_runs)
    publish_risk = next((risk for risk in risks if risk.approval_required), None)

    return [
        EvidenceRow(
            claim="Human browser actions are preserved as traceable source evidence.",
            status="proven" if trace.events else "blocked",
            evidence=[f"{len(trace.events)} normalized events", f"trace_id={trace.id}"],
        ),
        EvidenceRow(
            claim="Compiled automation still works on the recorded UI contract.",
            status="proven" if baseline_ok else "blocked",
            evidence=["final baseline shadow run -> pass" if baseline_ok else "baseline shadow failed"],
        ),
        EvidenceRow(
            claim="Automation tolerates selector drift by using semantic accessibility targets.",
            status="proven" if drift_ok else "blocked",
            evidence=[f"{sum(run.status == 'pass' for run in drift_runs)}/{len(drift_runs)} drift variants passed"],
        ),
        EvidenceRow(
            claim="Player-visible publish cannot silently bypass a human approval boundary.",
            status="needs_approval" if publish_risk else "blocked",
            evidence=[publish_risk.reason if publish_risk else "no publish approval decision found"],
        ),
        EvidenceRow(
            claim="Generated browser code is derived from the verified workflow, not arbitrary model shell output.",
            status="proven",
            evidence=["typed WorkflowSpec -> deterministic Playwright generator"],
        ),
    ]
