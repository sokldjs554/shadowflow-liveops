# ShadowFlow coding-agent contract

ShadowFlow turns observed browser work into a typed workflow, tests it in a synthetic shadow environment, and only then generates automation code.

Before editing:
1. Read `README.md`, `docs/JD_TRACEABILITY.md`, `docs/ARCHITECTURE.md`, and `docs/BOUNDARIES.md`.
2. Preserve the distinction between **model/compiler suggestions** and **deterministic verification authority**.
3. Do not weaken `shadowflow/engine/risk.py`, shadow variants, approval requirements, or tests just to make a proposed workflow pass.
4. Do not claim GameSpring private workflows, player data, or internal architecture. The live-ops scenario is synthetic and independently designed from public company/job information.
5. Do not add an open-source license or license badge. This portfolio repository is all-rights-reserved.

Before declaring work complete:
- `python -m pytest -q`
- `python -m ruff check shadowflow tests synthetic_app`
- `python -m mypy shadowflow`
- `tsc -p web/tsconfig.json --noEmit`
- `python -m shadowflow.cli demo`

Any measured number added to README must come from a committed script or CI/deployment artifact.
