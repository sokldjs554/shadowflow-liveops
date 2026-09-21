# ShadowFlow architecture

## Product boundary

ShadowFlow is a **workflow compiler**, not a general chatbot and not an autonomous browser agent. A human demonstrates a web workflow once. The system preserves the raw action trace, compiles it into a typed semantic workflow, runs that workflow against a synthetic digital twin with deliberate UI drift, repairs brittle targets, applies a deterministic side-effect policy, and finally generates guarded Playwright code.

```text
human demonstration
      │
      ▼
recorded TraceBundle ── redaction / provenance
      │
      ▼
WorkflowCompiler (LLM or deterministic demo)
      │        typed WorkflowSpec
      ▼
Deterministic risk policy
      │
      ├── baseline shadow twin
      ├── selector-drift twin #1
      ├── selector-drift twin #2
      └── selector-drift twin #3
                 │
         failures / evidence
                 ▼
          compiler repair
                 │
                 ▼
         same shadow matrix
                 │
                 ▼
  typed code generator + evidence packet
                 │
                 ▼
 human approval for player-visible publish
```

## Trust boundaries

### Compiler / LLM can
- abstract low-level browser events into workflow steps;
- propose semantic locators;
- repair a workflow from deterministic shadow failures;
- explain intent and provenance.

### Compiler / LLM cannot
- change the side-effect classification for publish;
- delete or weaken shadow variants;
- execute arbitrary shell commands;
- turn a failed shadow result into a pass;
- bypass the human approval token in generated automation.

The code generator is deterministic: verified `WorkflowSpec` becomes Playwright TypeScript. This deliberately separates **reasoning** from **execution authority**.

## Persistence

The demo uses SQLite WAL for run/evidence history because it gives a reproducible single-service deployment. The store interface is intentionally small enough to migrate to PostgreSQL if multi-instance writes become a measured need. No claim is made that SQLite is the production choice for a large deployment.
