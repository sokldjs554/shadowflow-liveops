# GameSpring AI Programmer JD traceability gate

Target: GameSpring — AI Programmer (AI system design & development), public Saramin posting reviewed on 2026-09-19.

This file is the feature gate for the project. At each major milestone, the job description must be reread and this table checked so novelty does not drift away from the role.

| Public job requirement | ShadowFlow artifact | Status |
|---|---|---|
| LLM-based service/tool that improves development or work productivity | one demonstrated web task -> reusable verified automation | implemented |
| Full-stack web application | browser product UI + FastAPI API + SQLite run/evidence store | implemented |
| LLM API integration | provider-neutral compiler + hosted Messages API adapter | implemented, real credential optional |
| Open-source model integration | OpenAI-compatible route for Ollama/vLLM/Qwen-style endpoints | implemented contract; real-model benchmark pending |
| Rapid prototyping | real browser-side recorder + preloaded demo trace both compile directly into workflow/code artifacts | implemented |
| AI agent / automation pipeline | normalize -> compile -> shadow -> repair -> risk gate -> codegen | implemented |
| Code generation | typed verified workflow -> generated Playwright TypeScript | implemented |
| Business-work automation | synthetic live-ops event-release workflow, no chat UI | implemented |
| Claude Code / Cursor vibe-coding workflow | `CLAUDE.md`, `AGENTS.md`, `.cursor/rules/shadowflow.mdc`, measurable completion gates | implemented |
| Frontend and backend breadth | TypeScript product UI + Python/FastAPI backend | implemented |
| Fast result / proof | deterministic keyless demo + tests + evaluation artifacts + GitHub Actions matrix | implemented; CI verified on Python 3.11/3.12/3.13 |
| Solo 0→1 full-stack from planning to deployment | design/research/code/test/demo/CI + Render public service + exact-commit smoke | implemented and verified |
| Global AI documentation/trend absorption | English OSS research and provider contracts documented | implemented |

## Company-domain relevance without private-process guessing

Public GameSpring information describes a global online/mobile game studio serving users across many countries. ShadowFlow therefore uses a **synthetic multilingual live-ops release** as the visible demo because repeated admin workflows, localization, preview, and release approval are understandable game-production examples.

This is only a scenario choice. The repository explicitly does **not** claim GameSpring uses this process or these tools internally.

## Milestone re-check log

### Gate 1 — topic selection
- Kept: productivity AI, full-stack, LLM/open-model adapters, automation, code generation.
- Rejected: chatbot UI and generic browser agent because both are common and less directly demonstrative of business-work productivity.
- Added after company check: multilingual live-ops synthetic scenario to make the demo relevant to a global mobile-game studio.

### Gate 2 — core implementation
- Confirmed full-stack path, typed LLM boundary, open-model route, repair loop, and generated code.
- Added Claude/Cursor repository contracts because the posting explicitly names AI coding tools.
- Deployment/evidence remain required before application materials are written.

### Gate 3 — demo and evaluation
- Re-read the posting before demo hardening. The product still directly covers work-productivity AI, full-stack web, LLM/open-model integration, automation, code generation, and fast prototyping.
- Added an actual browser-side recorder lab so the demo is not only a pre-baked pipeline.
- Added synthetic selector-drift evaluation and one semantic-drift limitation probe; this keeps the unusual project angle while showing failure boundaries instead of only successful cases.
- Kept application materials out of scope until GitHub/CI/public deployment evidence exists.

### Gate 4 — pre-GitHub handoff
- Re-read the public GameSpring AI Programmer posting again before repository handoff.
- Confirmed all three primary duties remain represented: productivity AI service/tooling, LLM/open-model full-stack web, and AI/code-generation/business-automation pipeline.
- Confirmed all named core capabilities remain represented: Claude/Cursor-style AI coding workflow, frontend/backend breadth, and fast proof through a runnable demo.
- Confirmed the preferred 0→1 solo full-stack story now has planning, research, implementation, tests, evaluation, CI, and Render configuration; only creation of the new GitHub remote and public deployment remain.


### Gate 5 — GitHub CI verification (2026-09-21)
- Re-read the currently open public GameSpring posting before treating the repository as implementation-complete. The current listing (2026-09-14 to 2026-11-13) still emphasizes the same three duties: LLM-based productivity tooling, full-stack web services combining LLM APIs/open-source models, and AI-agent/code-generation/business-automation pipelines.
- Reconfirmed the named capability requirements: Claude Code/Cursor-style AI coding, frontend/backend breadth, and proving results quickly with AI tools.
- Reconfirmed the preferred evidence: a solo AI full-stack project carried from planning through deployment, related technical grounding, and the ability to absorb current English AI documentation/trends.
- GitHub CI now verifies installation, tests, Ruff, mypy, strict TypeScript, and the keyless end-to-end compiler/shadow/repair/code-generation gate on Python 3.11, 3.12, and 3.13.
- CI exposed real static-quality defects (unused imports and two typing violations). They were fixed in the implementation rather than weakening the gates.
- Public deployment and exact-deployed-commit smoke verification remain required before application materials can be written.


### Gate 6 — public deployment and exact-commit smoke (2026-09-21)
- Rechecked the target GameSpring posting requirements before closing the project gate: productivity-focused LLM tooling, full-stack web delivery with LLM/open-model integration, and AI-agent/code-generation/work-automation pipelines remain the primary fit criteria.
- Reconfirmed the implementation evidence rather than adding a chat surface: recorded browser demonstration, typed workflow compilation, deterministic risk policy, adversarial shadow twins, repair, Playwright generation, and explicit human approval for player-visible side effects.
- Render deployment is live at `https://shadowflow-liveops.onrender.com`.
- The independent live-smoke workflow waited for the deployed `/api/release` commit `824eda232c027f5142ba3ef68aa6bdd1dac8c3b2`, then exercised the public API end to end.
- Deployed result: `ready_with_approval`, 2 compile/repair attempts, initial shadow matrix 1/4, repaired matrix 4/4, approval gates 1.
- Repository CI and live-smoke evidence are now both green. The project remains explicit that its LiveOps UI, traces, and workflows are synthetic and do not infer GameSpring's private systems.
- Project/demo/deployment gates are complete. Application materials may be written only after the final README/documentation commit also passes CI and exact-commit live smoke.
