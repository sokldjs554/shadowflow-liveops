from __future__ import annotations

from shadowflow.compiler.deterministic import DeterministicDemoCompiler
from shadowflow.engine.shadow import execute_shadow
from shadowflow.engine.trace import synthetic_liveops_trace


def test_shadow_drift_fails_before_semantic_repair() -> None:
    compiler = DeterministicDemoCompiler()
    trace = synthetic_liveops_trace()
    workflow = compiler.compile(trace)

    baseline = execute_shadow(workflow, variant="baseline")
    drift = execute_shadow(workflow, variant="selector-drift-7")

    assert baseline.status == "pass"
    assert drift.status == "fail"
    assert drift.failures[0].code == "target_not_found"


def test_semantic_repair_survives_multiple_dom_id_changes() -> None:
    compiler = DeterministicDemoCompiler()
    trace = synthetic_liveops_trace()
    workflow = compiler.compile(trace)
    first = execute_shadow(workflow, variant="selector-drift-1")
    repaired = compiler.repair(trace, workflow, first.failures)

    for seed in range(1, 13):
        run = execute_shadow(repaired, variant=f"selector-drift-{seed}")
        assert run.status == "pass", (seed, run.failures)
