from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from shadowflow.engine.pipeline import ShadowFlowPipeline
from shadowflow.engine.trace import synthetic_liveops_trace
from shadowflow.models import TraceBundle
from shadowflow.store import RunStore

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = Path(os.getenv("SHADOWFLOW_STATE_DIR", PROJECT_ROOT / ".shadowflow"))
STORE = RunStore(STATE_DIR / "runs.db")
PIPELINE = ShadowFlowPipeline(PROJECT_ROOT, STORE)
EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="shadowflow")

app = FastAPI(
    title="ShadowFlow",
    version="0.1.0",
    description="Human workflow to verified browser automation compiler with shadow execution.",
)


class RunRequest(BaseModel):
    trace: TraceBundle
    provider: str = "deterministic-demo"


class ApprovalRequest(BaseModel):
    actor: str = Field(min_length=2, max_length=80)
    reason: str = Field(min_length=4, max_length=500)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "shadowflow", "version": "0.1.0"}


@app.get("/api/release")
def release() -> dict[str, str]:
    return {
        "service": "shadowflow",
        "version": "0.1.0",
        "commit": os.getenv("RENDER_GIT_COMMIT", "unknown"),
    }


@app.get("/api/demo/trace")
def demo_trace() -> dict[str, object]:
    return synthetic_liveops_trace().model_dump(mode="json")


@app.post("/api/runs", status_code=202)
def create_run(body: RunRequest) -> dict[str, str]:
    if body.provider not in {"deterministic-demo", "openai-compatible", "ollama", "anthropic"}:
        raise HTTPException(status_code=400, detail="Unsupported provider")
    run_id = PIPELINE.start(body.provider)
    EXECUTOR.submit(PIPELINE.execute, run_id, body.trace)
    return {"id": run_id, "stage": "queued"}


@app.get("/api/runs")
def list_runs() -> dict[str, object]:
    return {"items": [item.model_dump(mode="json") for item in STORE.list()]}


@app.get("/api/runs/{run_id}")
def get_run(run_id: str) -> dict[str, object]:
    try:
        return STORE.get(run_id).model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@app.post("/api/runs/{run_id}/approve")
def approve_run(run_id: str, body: ApprovalRequest) -> dict[str, object]:
    try:
        packet = PIPELINE.approve(run_id, actor=body.actor, reason=body.reason)
        return packet.model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


STATIC = PROJECT_ROOT / "shadowflow" / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")
