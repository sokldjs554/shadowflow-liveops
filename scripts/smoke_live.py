from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

BASE_URL = os.getenv("BASE_URL", "https://shadowflow-liveops.onrender.com").rstrip("/")
EXPECTED_COMMIT = os.getenv("EXPECTED_COMMIT", "").strip()
TIMEOUT_SECONDS = int(os.getenv("SMOKE_TIMEOUT_SECONDS", "600"))


def request_json(path: str, method: str = "GET", payload: dict[str, object] | None = None) -> dict[str, object]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        BASE_URL + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "User-Agent": "shadowflow-live-smoke/1"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_for_release(deadline: float) -> dict[str, object]:
    last: object = None
    while time.monotonic() < deadline:
        try:
            release = request_json("/api/release")
            last = release
            commit = str(release.get("commit", ""))
            if not EXPECTED_COMMIT or commit == EXPECTED_COMMIT:
                return release
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            last = repr(exc)
        time.sleep(5)
    raise RuntimeError(f"deployment did not reach expected commit {EXPECTED_COMMIT!r}; last={last!r}")


def main() -> None:
    deadline = time.monotonic() + TIMEOUT_SECONDS
    release = wait_for_release(deadline)
    health = request_json("/api/health")
    assert health.get("status") == "ok", health
    trace = request_json("/api/demo/trace")
    created = request_json(
        "/api/runs",
        method="POST",
        payload={"trace": trace, "provider": "deterministic-demo"},
    )
    run_id = str(created["id"])

    record: dict[str, object] | None = None
    while time.monotonic() < deadline:
        record = request_json("/api/runs/" + run_id)
        if record.get("stage") in {"complete", "failed"}:
            break
        time.sleep(1)
    if record is None or record.get("stage") != "complete":
        raise RuntimeError(f"live run did not complete: {record!r}")

    packet = record.get("packet")
    if not isinstance(packet, dict):
        raise RuntimeError(f"missing merge packet: {record!r}")
    attempts = packet.get("attempts")
    assert packet.get("verdict") == "ready_with_approval", packet
    assert isinstance(attempts, list) and len(attempts) == 2, attempts
    assert attempts[0]["passed_variants"] == 1, attempts[0]
    assert attempts[1]["passed_variants"] == 4, attempts[1]
    assert packet["metrics"]["approval_gates"] == 1, packet["metrics"]
    assert "requireHumanApproval" in packet["generated"]["content"], packet["generated"]

    print(
        json.dumps(
            {
                "release": release,
                "run_id": run_id,
                "verdict": packet["verdict"],
                "attempts": len(attempts),
                "first_shadow": "1/4",
                "final_shadow": "4/4",
                "approval_gates": 1,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
