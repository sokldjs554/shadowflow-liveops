# AI-assisted development workflow

The role explicitly values modern AI coding tools. This repository makes that workflow reviewable instead of merely writing "used Claude/Cursor" in a resume.

1. Read the public JD gate before a major scope change.
2. AI may propose architecture/code/tests, but repository trust rules remain in `CLAUDE.md`, `AGENTS.md`, and `.cursor/rules/`.
3. Every generated change must pass Python tests, Ruff, mypy, and TypeScript type checking.
4. Project metrics come from committed evaluation scripts or CI/deployment logs.
5. LLM/open-model integration is kept behind one compiler contract so a provider swap does not alter risk authority.
6. Failures are retained and documented; a green result is not produced by weakening the checker.
