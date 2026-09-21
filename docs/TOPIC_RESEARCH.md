# Public-project collision audit

Research date: 2026-09-19

The project was intentionally chosen after checking common public approaches around browser agents and RPA. The goal is not to claim that nobody has ever combined these ideas; it is to avoid presenting another ordinary "LLM controls a browser" portfolio demo.

## Adjacent public projects reviewed

### Skyvern — `Skyvern-AI/skyvern`
Public positioning: LLM/computer-vision browser automation, Playwright-compatible SDK, and no-code workflow builder. Its strength is autonomous interaction with websites and resilience relative to hand-written XPath automation.

**Not copied:** ShadowFlow does not start from a natural-language task and autonomously solve an arbitrary website. It starts from a human demonstration and treats the trace as evidence.

### Browser Use — `browser-use/browser-use`
Public positioning: an open-source browser agent that navigates the web from tasks using an LLM and browser runtime.

**Not copied:** ShadowFlow's primary artifact is a reviewable typed workflow + evidence packet + generated automation, not an agent conversation/history.

### AI Workflow Recorder — `OwerLopez/ai-workflow-recorder`
Public positioning: browser telemetry, pattern analysis, workflow graph, and browser replay through an extension.

**Collision found:** recording user actions and replaying workflows is already a public theme. A recorder alone would therefore be too common for this portfolio.

**ShadowFlow difference:** it intentionally challenges the first replay against changed DOM identifiers, repairs it using recorded accessibility semantics, classifies side effects outside the model, and requires human approval before export of player-visible automation.

### Browserbase Open Operator / Stagehand
Public positioning: natural language -> browser operations using a browser runtime and LLM.

**Not copied:** ShadowFlow is not a prompt-to-browser operator. The differentiator is demonstration -> typed compiler -> adversarial shadow variants -> deterministic gate -> code artifact.

## Rejected common portfolio directions

- generic RAG chatbot;
- chat-based coding assistant;
- prompt -> browser agent;
- selector macro recorder;
- one-shot "generate Playwright from text";
- generic n8n-style workflow builder.

## Chosen novelty axis

The project concentrates on **workflow compilation under drift and side-effect constraints**:

1. human demonstration is source evidence;
2. raw actions are compiled, not blindly replayed;
3. the first brittle workflow is expected to fail a changed UI twin;
4. the repair must use evidence already captured in the demonstration;
5. the model/compiler cannot grade itself;
6. irreversible or player-visible effects are first-class review boundaries;
7. only a verified typed workflow can become generated code.
