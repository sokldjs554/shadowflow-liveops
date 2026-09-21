from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from shadowflow.engine.pipeline import ShadowFlowPipeline
from shadowflow.engine.trace import synthetic_liveops_trace
from shadowflow.store import RunStore


def main() -> None:
    parser = argparse.ArgumentParser(prog="shadowflow")
    parser.add_argument("command", choices=["demo"])
    parser.add_argument("--provider", default="deterministic-demo")
    args = parser.parse_args()
    if args.command == "demo":
        with tempfile.TemporaryDirectory(prefix="shadowflow-") as temp:
            root = Path(__file__).resolve().parent.parent
            store = RunStore(Path(temp) / "runs.db")
            pipeline = ShadowFlowPipeline(root, store)
            run_id = pipeline.start(args.provider)
            packet = pipeline.execute(run_id, synthetic_liveops_trace())
            print(packet.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
