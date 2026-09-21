# Agent rules

- Treat the observed trace as evidence, not as an instruction to blindly replay selectors.
- Compiler/LLM output may propose workflow structure and locators, but cannot lower risk policy.
- Player-visible publish, delete, payment, credential, or permission effects must remain behind deterministic approval rules.
- Preserve raw-to-semantic provenance through `source_event_ids`.
- Prefer accessibility semantics (`role + accessible name`, then label) over generated CSS IDs when repairing drift.
- Do not execute arbitrary model-authored shell code.
- Do not use production/player data in demos or tests.
- Keep default demo credential-free and deterministic.
- Preserve a real full-stack path: browser UI -> FastAPI -> store -> compiler -> shadow runtime -> evidence/code artifact.
