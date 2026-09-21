from __future__ import annotations

import time

from fastapi.testclient import TestClient

from shadowflow.main import app


def test_api_runs_demo_end_to_end() -> None:
    client = TestClient(app)
    trace = client.get("/api/demo/trace").json()
    created = client.post("/api/runs", json={"trace": trace, "provider": "deterministic-demo"})
    assert created.status_code == 202
    run_id = created.json()["id"]

    record = None
    for _ in range(100):
        record = client.get(f"/api/runs/{run_id}").json()
        if record["stage"] in {"complete", "failed"}:
            break
        time.sleep(0.03)

    assert record is not None
    assert record["stage"] == "complete"
    assert record["packet"]["verdict"] == "ready_with_approval"
    assert record["packet"]["metrics"]["shadow_passed"] == 4

    approved = client.post(
        f"/api/runs/{run_id}/approve",
        json={"actor": "test-reviewer", "reason": "reviewed shadow evidence"},
    )
    assert approved.status_code == 200
    assert approved.json()["verdict"] == "approved_for_export"
