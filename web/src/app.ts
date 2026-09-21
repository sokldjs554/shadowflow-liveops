type Stage =
  | 'queued'
  | 'normalizing'
  | 'compiling'
  | 'shadowing'
  | 'repairing'
  | 'generating'
  | 'complete'
  | 'failed';

type Locator = {
  strategy: 'selector' | 'role_name' | 'label' | 'text';
  selector?: string | null;
  role?: string | null;
  name?: string | null;
  label?: string | null;
  text?: string | null;
};

type StepExecution = {
  step_id: string;
  status: 'pass' | 'fail' | 'approval_required' | 'skipped';
  detail: string;
  resolved_target?: string | null;
};

type ShadowRun = {
  variant: string;
  status: 'pass' | 'fail' | 'approval_required';
  steps: StepExecution[];
  failures: Array<{ code: string; step_id?: string | null; message: string }>;
};

type WorkflowStep = {
  id: string;
  intent: string;
  action: string;
  locator?: Locator | null;
  approval_required: boolean;
  side_effect: string;
};

type Attempt = {
  number: number;
  summary: string;
  workflow: {
    version: number;
    steps: WorkflowStep[];
    warnings: string[];
  };
  shadow_runs: ShadowRun[];
  passed_variants: number;
  total_variants: number;
};

type Packet = {
  run_id: string;
  verdict: 'ready_with_approval' | 'approved_for_export' | 'blocked';
  trace: { id: string; title: string; events: Array<{ id: string; seq: number; action: string; target?: { accessible_name?: string | null } | null }> };
  attempts: Attempt[];
  risks: Array<{ step_id: string; side_effect: string; approval_required: boolean; reason: string }>;
  generated: { name: string; language: string; content: string; sha256: string };
  evidence: Array<{ claim: string; status: string; evidence: string[] }>;
  metrics: Record<string, number>;
  limitations: string[];
};

type RunRecord = {
  id: string;
  stage: Stage;
  status_message: string;
  provider: string;
  packet?: Packet | null;
  events: Array<{ at: string; stage: string; message: string }>;
  approval?: { actor: string; reason: string; scope: string } | null;
};

type TraceBundle = {
  id: string;
  title: string;
  source: string;
  events: Array<Record<string, unknown>>;
  redactions?: string[];
};

const $ = <T extends HTMLElement>(id: string): T => {
  const node = document.getElementById(id);
  if (!node) throw new Error(`Missing element #${id}`);
  return node as T;
};

const runButton = $<HTMLButtonElement>('run-demo');
const approveButton = $<HTMLButtonElement>('approve');
const statusLine = $('status-line');
const stagePill = $('stage-pill');
const traceGrid = $('trace-grid');
const workflowGrid = $('workflow-grid');
const matrix = $('matrix');
const evidence = $('evidence');
const riskPanel = $('risk-panel');
const codePanel = $('generated-code');
const eventLog = $('event-log');
const metricTrace = $('metric-trace');
const metricSteps = $('metric-steps');
const metricShadow = $('metric-shadow');
const metricApproval = $('metric-approval');
const sourceState = $('source-state');
const recordStartButton = $<HTMLButtonElement>('record-start');
const recordCompileButton = $<HTMLButtonElement>('record-compile');
const recorderStatus = $('recorder-status');

let currentRunId: string | null = null;
let currentPacket: Packet | null = null;
let recording = false;
let recordedEvents: Array<Record<string, unknown>> = [];
let recordSeq = 0;

function esc(value: unknown): string {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
}

function badge(status: string): string {
  const kind = status === 'pass' || status === 'proven' || status === 'approved_for_export'
    ? 'good'
    : status === 'fail' || status === 'blocked'
      ? 'bad'
      : 'warn';
  return `<span class="badge ${kind}">${esc(status.replaceAll('_', ' '))}</span>`;
}

async function jsonFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${response.status} ${text}`);
  }
  return await response.json() as T;
}

async function submitTrace(trace: TraceBundle): Promise<void> {
  runButton.disabled = true;
  recordCompileButton.disabled = true;
  approveButton.disabled = true;
  stagePill.textContent = 'queued';
  renderSource(trace);
  const created = await jsonFetch<{ id: string; stage: string }>('/api/runs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ trace, provider: 'deterministic-demo' }),
  });
  currentRunId = created.id;
  await pollRun(created.id);
}

async function runDemo(): Promise<void> {
  runButton.disabled = true;
  approveButton.disabled = true;
  stagePill.textContent = 'loading trace';
  statusLine.textContent = 'Loading a synthetic live-ops demonstration…';
  try {
    const trace = await jsonFetch<TraceBundle>('/api/demo/trace');
    await submitTrace(trace);
  } catch (error) {
    stagePill.textContent = 'failed';
    statusLine.textContent = error instanceof Error ? error.message : String(error);
    runButton.disabled = false;
  }
}

async function pollRun(runId: string): Promise<void> {
  for (let i = 0; i < 120; i += 1) {
    const record = await jsonFetch<RunRecord>(`/api/runs/${runId}`);
    renderRun(record);
    if (record.stage === 'complete' || record.stage === 'failed') {
      runButton.disabled = false;
      return;
    }
    await new Promise(resolve => window.setTimeout(resolve, 450));
  }
  throw new Error('Run polling timed out.');
}

function renderSource(trace: TraceBundle): void {
  sourceState.innerHTML = `
    <div class="source-kicker">SYNTHETIC LIVE-OPS WORKSPACE</div>
    <h3>${esc(trace.title)}</h3>
    <p>One demonstrated release: event setup → locale copy → UTC schedule → banner → preview → publish.</p>
    <div class="mini-flow">
      <span>record</span><i>→</i><span>compile</span><i>→</i><span>shadow</span><i>→</i><span>repair</span><i>→</i><span>approve</span>
    </div>
  `;
}

function renderRun(record: RunRecord): void {
  stagePill.textContent = record.stage;
  statusLine.textContent = record.status_message;
  renderEvents(record.events);
  if (record.packet) {
    currentPacket = record.packet;
    renderPacket(record.packet, record.approval ?? null);
  }
}

function renderEvents(events: RunRecord['events']): void {
  eventLog.innerHTML = events.slice(-8).map(item => `
    <div class="log-row">
      <span class="log-stage">${esc(item.stage)}</span>
      <span>${esc(item.message)}</span>
    </div>
  `).join('');
}

function renderPacket(packet: Packet, approval: RunRecord['approval']): void {
  const finalAttempt = packet.attempts[packet.attempts.length - 1];
  metricTrace.textContent = String(packet.metrics.trace_events ?? packet.trace.events.length);
  metricSteps.textContent = String(packet.metrics.workflow_steps ?? finalAttempt.workflow.steps.length);
  metricShadow.textContent = `${packet.metrics.shadow_passed}/${packet.metrics.shadow_variants}`;
  metricApproval.textContent = String(packet.metrics.approval_gates ?? 0);

  traceGrid.innerHTML = packet.trace.events.map((item, index) => {
    const target = item.target?.accessible_name ?? 'page';
    return `<div class="trace-chip"><b>${index + 1}</b><span>${esc(item.action)}</span><small>${esc(target)}</small></div>`;
  }).join('');

  workflowGrid.innerHTML = finalAttempt.workflow.steps.map(step => {
    const locator = step.locator?.strategy === 'role_name'
      ? `${step.locator.role}:${step.locator.name}`
      : step.locator?.selector ?? step.locator?.strategy ?? 'none';
    return `
      <article class="step-card ${step.approval_required ? 'approval-step' : ''}">
        <div class="step-head"><span>${esc(step.id)}</span>${step.approval_required ? badge('approval') : ''}</div>
        <h4>${esc(step.intent)}</h4>
        <p>${esc(step.action)} · ${esc(step.side_effect)}</p>
        <code>${esc(locator)}</code>
      </article>`;
  }).join('');

  const variants = Array.from(new Set(packet.attempts.flatMap(attempt => attempt.shadow_runs.map(run => run.variant))));
  matrix.innerHTML = `
    <div class="matrix-row matrix-head"><span>attempt</span>${variants.map(v => `<span>${esc(v)}</span>`).join('')}</div>
    ${packet.attempts.map(attempt => `
      <div class="matrix-row">
        <span><b>#${attempt.number}</b><small>${esc(attempt.summary)}</small></span>
        ${variants.map(variant => {
          const run = attempt.shadow_runs.find(item => item.variant === variant);
          return `<span>${run ? badge(run.status) : '—'}</span>`;
        }).join('')}
      </div>`).join('')}
  `;

  evidence.innerHTML = packet.evidence.map(row => `
    <article class="evidence-row">
      <div>${badge(row.status)}</div>
      <div><h4>${esc(row.claim)}</h4><p>${row.evidence.map(esc).join(' · ')}</p></div>
    </article>
  `).join('');

  const approvalRisk = packet.risks.find(item => item.approval_required);
  riskPanel.innerHTML = approvalRisk ? `
    <div class="risk-icon">!</div>
    <div>
      <h3>Human gate before player-visible publish</h3>
      <p>${esc(approvalRisk.reason)}</p>
      <div class="risk-meta">step ${esc(approvalRisk.step_id)} · ${esc(approvalRisk.side_effect)}</div>
      ${approval ? `<div class="approval-note">Approved by ${esc(approval.actor)} — ${esc(approval.reason)}</div>` : ''}
    </div>
  ` : '<p>No approval gate found.</p>';

  codePanel.textContent = packet.generated.content;
  approveButton.disabled = packet.verdict !== 'ready_with_approval';
  approveButton.textContent = packet.verdict === 'approved_for_export' ? 'Approved for export' : 'Approve generated automation';
  stagePill.textContent = packet.verdict.replaceAll('_', ' ');
}

function targetFor(element: HTMLElement): Record<string, unknown> {
  const name = element.getAttribute('aria-label') ?? element.textContent?.trim() ?? element.id;
  return {
    selector: element.id ? `#${element.id}` : null,
    role: element.dataset.role ?? null,
    accessible_name: name,
    label: element.getAttribute('aria-label') ?? null,
    text: element.textContent?.trim() || null,
    test_id: null,
  };
}

function recordAction(action: string, element: HTMLElement | null, value: unknown = null): void {
  if (!recording) return;
  recordedEvents.push({
    id: `recorded-${String(recordSeq).padStart(2, '0')}`,
    seq: recordSeq,
    at: new Date().toISOString(),
    page: '/synthetic-liveops/events/new',
    action,
    target: element ? targetFor(element) : null,
    value,
    before_hash: null,
    after_hash: null,
    metadata: { browser_recorder: true },
  });
  recordSeq += 1;
  recorderStatus.textContent = `Recording · ${recordedEvents.length} actions captured`;
  recordCompileButton.disabled = recordedEvents.length < 2;
}

function startRecording(): void {
  recording = true;
  recordedEvents = [];
  recordSeq = 0;
  recordAction('navigate', null, '/synthetic-liveops/events/new');
  recordStartButton.textContent = 'Restart recording';
  recordCompileButton.disabled = true;
  recorderStatus.textContent = 'Recording. Edit fields, preview, and publish inside the synthetic workspace.';
}

async function compileRecorded(): Promise<void> {
  if (!recordedEvents.length) return;
  recording = false;
  const trace: TraceBundle = {
    id: `recorded-${Date.now()}`,
    title: 'Browser-recorded synthetic live-ops workflow',
    source: 'recorded',
    events: recordedEvents,
    redactions: [],
  };
  recorderStatus.textContent = `Captured ${recordedEvents.length} actions. Compiling and shadow-testing…`;
  try {
    await submitTrace(trace);
  } catch (error) {
    statusLine.textContent = error instanceof Error ? error.message : String(error);
    runButton.disabled = false;
    recordCompileButton.disabled = false;
  }
}

function bindRecorder(): void {
  const inputs = [
    'event-name-v17', 'locale-ko-v17', 'locale-ja-v17', 'locale-en-v17', 'start-at-v17', 'end-at-v17',
  ];
  for (const id of inputs) {
    const element = $<HTMLInputElement>(id);
    element.addEventListener('change', () => recordAction('input', element, element.value));
  }
  const regions = $<HTMLSelectElement>('regions-v17');
  regions.addEventListener('change', () => {
    const values = Array.from(regions.selectedOptions).map(option => option.value);
    recordAction('select', regions, values);
  });
  const banner = $<HTMLButtonElement>('banner-v17');
  banner.addEventListener('click', () => {
    recordAction('upload', banner, 'fixtures/autumn-banner.webp');
    recorderStatus.textContent = `Recording · demo banner staged · ${recordedEvents.length} actions captured`;
  });
  const preview = $<HTMLButtonElement>('preview-v17');
  preview.addEventListener('click', () => recordAction('preview', preview, null));
  const publish = $<HTMLButtonElement>('publish-v17');
  publish.addEventListener('click', () => {
    recordAction('publish', publish, null);
    recorderStatus.textContent = 'Publish was recorded as intent only. No external action was executed.';
  });
  recordStartButton.addEventListener('click', startRecording);
  recordCompileButton.addEventListener('click', () => { void compileRecorded(); });
}

async function approve(): Promise<void> {
  if (!currentRunId || !currentPacket) return;
  approveButton.disabled = true;
  const packet = await jsonFetch<Packet>(`/api/runs/${currentRunId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ actor: 'demo-reviewer', reason: 'Shadow variants passed; export the generated automation only.' }),
  });
  currentPacket = packet;
  const record = await jsonFetch<RunRecord>(`/api/runs/${currentRunId}`);
  renderRun(record);
}

runButton.addEventListener('click', () => { void runDemo(); });
approveButton.addEventListener('click', () => { void approve(); });
bindRecorder();

void jsonFetch<{ status: string }>('/api/health')
  .then(() => { statusLine.textContent = 'Ready. Run the synthetic demonstration to compile a human workflow.'; })
  .catch(() => { statusLine.textContent = 'Backend is not reachable.'; });
