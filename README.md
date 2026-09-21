# ShadowFlow

[![ci](https://github.com/sokldjs554/shadowflow-liveops/actions/workflows/ci.yml/badge.svg)](https://github.com/sokldjs554/shadowflow-liveops/actions/workflows/ci.yml)
[![live smoke](https://github.com/sokldjs554/shadowflow-liveops/actions/workflows/live-smoke.yml/badge.svg)](https://github.com/sokldjs554/shadowflow-liveops/actions/workflows/live-smoke.yml)

> **Observe a web workflow once, compile it into a typed automation, challenge it against UI drift in a shadow twin, and generate code only after deterministic verification.**

**Live demo:** https://shadowflow-liveops.onrender.com  
**Repository:** https://github.com/sokldjs554/shadowflow-liveops

ShadowFlow is a full-stack AI workflow compiler. It is deliberately **not a chatbot** and **not another prompt-driven browser agent**.

The product uses a synthetic multilingual game live-ops workflow to demonstrate a general work-productivity problem: recorded browser actions are easy to automate badly. Generated selectors drift, side effects get hidden inside agent loops, and the same model that authored an automation should not be the only thing grading it.

## Product flow

```text
human demonstration
   -> trace + provenance + redaction
   -> LLM/compiler WorkflowSpec
   -> deterministic side-effect policy
   -> baseline + UI-drift shadow twins
   -> failure evidence
   -> semantic repair
   -> same shadow matrix
   -> guarded Playwright generation
   -> human approval for player-visible export
```

## What is different

Public browser-agent projects already cover natural-language navigation, vision-based browser control, no-code workflow builders, and macro-style recording. ShadowFlow focuses on a narrower failure mode: **can a demonstrated workflow be promoted into durable automation when UI selectors drift, without letting the compiler grade its own side effects?**

The default demo intentionally compiles a brittle selector-based workflow first. It must fail changed-DOM twins. The repair is allowed to use the accessibility semantics captured in the original human trace, but it cannot disable the shadow variants or the publish approval gate.

## Demo

The deployed product is available at **https://shadowflow-liveops.onrender.com**. The default path is credential-free, so a reviewer can run the full compile → shadow rejection → semantic repair → code generation flow without supplying a model key.

```bash
python -m pip install -e ".[dev]"
python -m shadowflow.cli demo
uvicorn shadowflow.main:app --reload
```

Open `http://127.0.0.1:8000`. Use **Run demonstration** for the fast path, or **Recorder lab** to capture your own actions inside the synthetic workspace and compile that trace.

The default route is credential-free and deterministic so the full compile/shadow/repair/codegen path can be reproduced. Optional LLM routes include an OpenAI-compatible endpoint for Ollama/vLLM/Qwen-style serving and a hosted Messages API adapter.

## Stack

- Python 3.11+ / FastAPI / Pydantic v2 / SQLite WAL
- TypeScript browser UI, strict compiler settings, no chat UI
- provider-neutral workflow compiler
- OpenAI-compatible local/open-model adapter
- hosted Messages API adapter
- typed synthetic digital twin
- deterministic side-effect policy
- Playwright TypeScript code generator
- pytest / Ruff / mypy / TypeScript typecheck
- Render-ready single-service deployment

## Trust boundaries

The compiler can propose workflow semantics and repairs. It cannot:
- lower the publish risk classification;
- remove shadow variants;
- execute arbitrary shell commands;
- rewrite a failed shadow result;
- bypass the generated human-approval guard.

Sensitive-looking input fields are redacted before trace persistence.

## Verification

```bash
python -m pytest -q
python -m ruff check shadowflow tests synthetic_app
python -m mypy shadowflow
tsc -p web/tsconfig.json --noEmit
python scripts/evaluate.py
```

Measured on the current local synthetic evaluation (`artifacts/evaluation.json`):

| Check | Result |
|---|---:|
| Python tests | **9 passed** |
| Repeated deterministic acceptance | **5/5 `ready_with_approval`** |
| Brittle selector workflow on 24 changed-ID twins | **0/24 passed** |
| Evidence-based semantic repair on the same 24 twins | **24/24 passed** |
| Final pipeline shadow matrix | **4/4 passed** |
| Player-visible publish approval gates | **1** |
| Generated raw CSS locator count after repair | **0** |
| Deliberate accessible-name semantic drift probe | **fails/abstains instead of guessing** |

These are synthetic robustness measurements, not a claim about production browser-agent success or employee time savings. Real open-model quality has not yet been benchmarked.


## Deployed verification

A separate GitHub Actions job verifies the **actual Render deployment**, not just the repository build. It waits until `/api/release` reports the exact Git commit under review, submits the synthetic demonstration through the public API, polls the deployed run, and validates the final evidence packet.

Each successful `live-smoke` run verifies that `/api/release` matches the exact Git SHA under test before exercising the public API. A verified deployed run produced:

| Deployed check | Result |
|---|---:|
| Render release | **live** |
| Final verdict | **`ready_with_approval`** |
| Compile / repair attempts | **2** |
| Initial shadow matrix | **1/4 passed — rejected** |
| Repaired shadow matrix | **4/4 passed** |
| Player-visible approval gates | **1** |

The public service uses synthetic workflow data and ephemeral demo state. These results do not claim production traffic, production persistence, or real employee productivity gains.

## Documentation

- `docs/JD_TRACEABILITY.md` — GameSpring public posting -> concrete artifact and milestone gates
- `docs/TOPIC_RESEARCH.md` — public-project collision audit
- `docs/ARCHITECTURE.md` — trust boundaries and pipeline
- `docs/DEMO.md` — reviewer walkthrough
- `docs/EVALUATION.md` — measurement contract
- `docs/BOUNDARIES.md` — what the project does not claim
- `docs/AI_CODING_WORKFLOW.md` — Claude/Cursor-style development gates

## Scope

The live-ops workflow, UI state, localization content, and shadow variants are synthetic. This repository does not use or infer GameSpring's private code, admin tools, employee workflow, player data, or internal architecture.

Copyright © 2026 윤기혁. All rights reserved. Portfolio project.
