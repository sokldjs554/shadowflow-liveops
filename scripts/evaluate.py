from __future__ import annotations

import json
import platform
import statistics
import tempfile
import time
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shadowflow.compiler.deterministic import DeterministicDemoCompiler
from shadowflow.engine.pipeline import ShadowFlowPipeline
from shadowflow.engine.shadow import execute_shadow
from shadowflow.engine.trace import synthetic_liveops_trace
from shadowflow.store import RunStore

OUT = ROOT / "artifacts" / "evaluation.json"


def main() -> None:
    trace = synthetic_liveops_trace()
    compiler = DeterministicDemoCompiler()
    brittle = compiler.compile(trace)
    first_failure = execute_shadow(brittle, variant="selector-drift-1").failures
    repaired = compiler.repair(trace, brittle, first_failure)

    variants = [f"selector-drift-{seed}" for seed in range(1, 25)]
    brittle_runs = [execute_shadow(brittle, variant=variant) for variant in variants]
    repaired_runs = [execute_shadow(repaired, variant=variant) for variant in variants]
    semantic_drift = execute_shadow(repaired, variant="semantic-drift-publish")

    durations: list[float] = []
    acceptance: list[dict[str, object]] = []
    for index in range(5):
        with tempfile.TemporaryDirectory(prefix="shadowflow-eval-") as temp:
            store = RunStore(Path(temp) / "runs.db")
            pipeline = ShadowFlowPipeline(ROOT, store)
            run_id = pipeline.start("deterministic-demo")
            started = time.perf_counter()
            packet = pipeline.execute(run_id, trace)
            durations.append(time.perf_counter() - started)
            acceptance.append(
                {
                    "run": index + 1,
                    "verdict": packet.verdict,
                    "attempts": len(packet.attempts),
                    "final_shadow": f"{packet.attempts[-1].passed_variants}/{packet.attempts[-1].total_variants}",
                    "approval_gates": packet.metrics["approval_gates"],
                }
            )

    artifact = {
        "generated_at": datetime.now(UTC).isoformat(),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "synthetic_contract": {
            "trace_events": len(trace.events),
            "selector_drift_variants": len(variants),
            "semantic_drift_probe": 1,
        },
        "selector_drift": {
            "brittle_passes": sum(run.status == "pass" for run in brittle_runs),
            "brittle_total": len(brittle_runs),
            "repaired_passes": sum(run.status == "pass" for run in repaired_runs),
            "repaired_total": len(repaired_runs),
        },
        "semantic_drift_limit": {
            "status": semantic_drift.status,
            "failure_codes": [failure.code for failure in semantic_drift.failures],
            "note": "Expected limitation: when the accessible name itself changes, the v0.1 evidence cannot safely infer the new target and abstains/fails rather than guessing.",
        },
        "acceptance": acceptance,
        "pipeline_seconds": {
            "median": round(statistics.median(durations), 4),
            "min": round(min(durations), 4),
            "max": round(max(durations), 4),
        },
        "generated_code": {},
    }
    # Avoid deriving code claims from an implementation object; use the real packet artifact instead.
    with tempfile.TemporaryDirectory(prefix="shadowflow-codegen-") as temp:
        store = RunStore(Path(temp) / "runs.db")
        pipeline = ShadowFlowPipeline(ROOT, store)
        run_id = pipeline.start("deterministic-demo")
        packet = pipeline.execute(run_id, trace)
        artifact["generated_code"] = {
            "sha256": packet.generated.sha256,
            "uses_role_locator": "getByRole" in packet.generated.content,
            "uses_label_locator": "getByLabel" in packet.generated.content,
            "contains_approval_guard": "requireHumanApproval" in packet.generated.content,
            "raw_css_locator_count": packet.generated.content.count("page.locator(\"#"),
        }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(artifact, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
