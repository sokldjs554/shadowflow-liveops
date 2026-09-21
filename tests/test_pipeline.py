from __future__ import annotations

from pathlib import Path

from shadowflow.engine.pipeline import ShadowFlowPipeline
from shadowflow.engine.trace import synthetic_liveops_trace
from shadowflow.store import RunStore


def test_shadow_pipeline_rejects_brittle_selectors_then_repairs(tmp_path: Path) -> None:
    store = RunStore(tmp_path / "runs.db")
    pipeline = ShadowFlowPipeline(Path(__file__).resolve().parents[1], store)
    run_id = pipeline.start("deterministic-demo")
    packet = pipeline.execute(run_id, synthetic_liveops_trace())

    assert packet.verdict == "ready_with_approval"
    assert len(packet.attempts) == 2
    first, repaired = packet.attempts
    assert first.passed_variants == 1
    assert first.total_variants == 4
    assert repaired.passed_variants == 4
    assert repaired.total_variants == 4
    assert any(
        failure.code == "target_not_found"
        for run in first.shadow_runs
        for failure in run.failures
    )
    assert all(
        step.locator is None or step.locator.strategy != "selector"
        for step in repaired.workflow.steps
    )
    publish_risk = next(item for item in packet.risks if item.approval_required)
    assert publish_risk.side_effect.value == "external_write"
    assert "requireHumanApproval" in packet.generated.content
    assert "getByRole" in packet.generated.content
    assert "getByLabel" in packet.generated.content


def test_approval_changes_export_verdict_without_real_publish(tmp_path: Path) -> None:
    store = RunStore(tmp_path / "runs.db")
    pipeline = ShadowFlowPipeline(Path(__file__).resolve().parents[1], store)
    run_id = pipeline.start("deterministic-demo")
    pipeline.execute(run_id, synthetic_liveops_trace())

    packet = pipeline.approve(run_id, actor="reviewer", reason="shadow evidence reviewed")
    record = store.get(run_id)

    assert packet.verdict == "approved_for_export"
    assert record.approval is not None
    assert record.approval["scope"].startswith("generated automation export only")
