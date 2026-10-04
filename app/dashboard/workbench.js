import { demoGet, interactionPost, reportingGet } from './api.js';
import { element, duration, statusLabel, renderEventDetail } from './detail.js';

const $ = id => document.getElementById(id);
let metadata = null;
let catalog = [];
let selected = null;
let busy = false;
let active = false;
let generation = 0;
let metadataGeneration = 0;
let loaded = false;
let elapsedTimer;
const initialResult = 'Select a scenario or enter custom text.';

function view(interactions) {
  if (active === interactions) return;
  active = interactions;
  generation++;
  $('interactions-view').hidden = !interactions;
  $('overview-view').hidden = interactions;
  for (const [id, current] of [['nav-overview', !interactions], ['nav-interactions', interactions]]) {
    $(id).classList.toggle('active', current);
    if (current) $(id).setAttribute('aria-current', 'page'); else $(id).removeAttribute('aria-current');
  }
  if (!interactions) {
    $('custom-content').value = '';
    clearResult();
  } else {
    $('run-status').textContent = busy ? 'A submitted interaction is still pending. Its outcome is unknown until received.' : 'No interaction submitted.';
  }
  updateControls();
  document.dispatchEvent(new Event('console-view'));
}
$('nav-overview').addEventListener('click', () => view(false));
$('nav-interactions').addEventListener('click', () => view(true));

function validInput() {
  const text = $('custom-content').value;
  const chars = [...text];
  const surrogate = chars.some(c => c.length === 1 && c.charCodeAt(0) >= 0xd800 && c.charCodeAt(0) <= 0xdfff);
  $('input-count').textContent = `${chars.length.toLocaleString()} / 16,384 characters`;
  $('input-validation').textContent = surrogate ? 'Invalid Unicode character.' : chars.length > 16384 ? 'Character limit exceeded.' : '';
  return chars.length > 0 && chars.length <= 16384 && !surrogate;
}
function updateControls() {
  const inputValid = validInput();
  $('custom-content').disabled = busy;
  $('custom-target').disabled = busy || !loaded;
  $('reload-workspace').disabled = busy;
  $('run-custom').disabled = busy || !loaded || !inputValid || !metadata?.custom.targets.some(t => t.target_id === $('custom-target').value);
  document.querySelectorAll('[data-scenario]').forEach(button => { button.disabled = busy || !loaded || !catalog.find(s => s.id === button.dataset.scenario)?.enabled; });
  if ($('run-scenario')) $('run-scenario').disabled = busy || !loaded || !selected?.enabled;
}
function targetDescription() {
  const target = metadata?.custom.targets.find(t => t.target_id === $('custom-target').value);
  $('target-description').textContent = target?.target_id === 'local-echo' ? 'Returns approved input. No generation call; enabled semantic controls still run.' : target ? `Configured model: ${target.model_id ?? 'not recorded'}. Runtime availability is checked only when you run.` : 'No registered public target available.';
}
$('custom-content').addEventListener('input', updateControls);
$('custom-target').addEventListener('change', targetDescription);

function clearResult() {
  clearInterval(elapsedTimer);
  $('run-context').textContent = initialResult;
  $('run-status').textContent = 'No interaction submitted.';
  $('run-result').replaceChildren();
  $('run-pipeline').replaceChildren();
  $('run-evidence').replaceChildren();
  $('scenario-selection').replaceChildren();
  selected = null;
  document.querySelectorAll('[data-scenario]').forEach(button => (button.classList.remove('selected'), button.setAttribute('aria-pressed', 'false')));
}
function selectScenario(scenario) {
  if (busy) return;
  clearResult();
  selected = scenario;
  $('run-context').textContent = `Scenario profile: ${scenario.profile}`;
  const description = element('p', '', scenario.description);
  const expected = element('p', '', `Expected: ${scenario.expected_error ?? scenario.expected_action}${scenario.expected_codes.length ? ` · ${scenario.expected_codes.join(', ')}` : ''}`);
  const run = element('button', 'button primary', 'Run scenario'); run.type = 'button'; run.id = 'run-scenario';
  run.addEventListener('click', () => execute({ scenario_id: scenario.id }, { scenario, target: 'local-ollama' }));
  $('scenario-selection').append(description, expected);
  if (scenario.simulation) $('scenario-selection').append(element('p', 'simulation-label', 'Controlled unavailable-transport simulation'));
  if (scenario.prerequisite) $('scenario-selection').append(element('p', 'muted', scenario.prerequisite));
  $('scenario-selection').append(run);
  document.querySelectorAll('[data-scenario]').forEach(button => (button.classList.toggle('selected', button.dataset.scenario === scenario.id), button.setAttribute('aria-pressed', String(button.dataset.scenario === scenario.id))));
  updateControls();
}
function renderCatalog() {
  const nodes = [];
  for (const category of ['Benign', 'Deterministic', 'Semantic', 'Failure modes']) {
    nodes.push(element('h3', '', category));
    for (const scenario of catalog.filter(s => s.category === category)) {
      const button = element('button', 'scenario-item'); button.type = 'button'; button.dataset.scenario = scenario.id; button.setAttribute('aria-pressed', 'false');
      button.append(element('strong', '', scenario.title), element('small', '', scenario.enabled ? `Expected ${scenario.expected_error ?? scenario.expected_action}` : scenario.prerequisite));
      if (scenario.simulation) button.append(element('small', 'simulation-label', 'Controlled simulation'));
      button.addEventListener('click', () => selectScenario(scenario)); nodes.push(button);
    }
  }
  $('scenario-list').replaceChildren(...nodes);
}
async function loadWorkspace() {
  if (busy) return;
  const token = ++metadataGeneration;
  loaded = false; metadata = null; catalog = [];
  $('workspace-availability').textContent = 'Loading configured controls…';
  $('custom-controls').replaceChildren(); $('custom-policy').textContent = '';
  $('custom-target').replaceChildren(); $('target-description').textContent = 'Configuration unavailable.';
  $('scenario-list').replaceChildren(); clearResult(); updateControls();
  const results = await Promise.allSettled([demoGet('workspace'), demoGet('scenarios')]);
  if (token !== metadataGeneration) return;
  const disabled = results.every(r => r.status === 'rejected' && r.reason.status === 404);
  $('nav-interactions').hidden = disabled;
  if (disabled) { if (active) view(false); return; }
  if (results.some(r => r.status !== 'fulfilled')) {
    $('workspace-availability').textContent = 'Workspace configuration unavailable. Run is disabled. Reload configuration to try again.';
    updateControls(); return;
  }
  metadata = results[0].value; catalog = results[1].value.items; loaded = true;
  const targets = [...metadata.custom.targets].sort((a, b) => a.target_id === 'local-echo' ? -1 : b.target_id === 'local-echo' ? 1 : 0);
  $('custom-target').replaceChildren(...targets.map(t => { const option = element('option', '', t.target_id === 'local-echo' ? 'Local echo' : 'Local model'); option.value = t.target_id; return option; }));
  for (const control of metadata.custom.controls) {
    const row = element('div', 'control-row'); row.append(element('span', '', control.control_id), element('span', '', control.enabled ? 'Enabled' : 'Disabled')); $('custom-controls').append(row);
  }
  $('custom-policy').textContent = `Policy ${metadata.custom.policy_digest}`;
  $('workspace-availability').textContent = 'Configured controls and targets · availability is determined when you run.';
  renderCatalog(); targetDescription(); updateControls();
  if (location.hash === '#interactions' && !active) view(true);
}
$('reload-workspace').addEventListener('click', loadWorkspace);
$('custom-form').addEventListener('submit', event => {
  event.preventDefault();
  if ($('run-custom').disabled) return;
  execute({ target_id: $('custom-target').value, content: $('custom-content').value }, { target: $('custom-target').value });
});

function stage(list, name, text) { const node = element('li'); node.append(element('strong', '', name), element('span', '', text)); list.append(node); }
function pipeline(view, payload) {
  const list = element('ol', 'pipeline-list');
  stage(list, 'Input', 'Submitted through the interaction gateway. Content is excluded from audit history.');
  if (!view) {
    stage(list, 'Recorded pipeline', 'Reporting evidence unavailable. No recorded stage or invocation is inferred.');
  } else {
    const e = view.event;
    stage(list, 'Deterministic controls', e.control_status.filter(([id]) => id !== 'semantic-security').map(([id, enabled]) => `${id}: ${!enabled ? 'disabled' : e.evaluated_controls.includes(id) ? 'completed' : 'not completed'}`).join(' · '));
    const semanticEnabled = e.control_status.some(([id, enabled]) => id === 'semantic-security' && enabled);
    stage(list, 'Semantic evaluator', `${e.semantic_status ?? (semanticEnabled ? 'Not attempted / not recorded' : 'Disabled')} · evaluator ${e.semantic_model_id ?? 'not recorded'} · ${duration(e.semantic_duration_ms)}`);
    stage(list, 'Findings', e.action === null ? 'Partial findings not recorded for operational failure.' : e.findings.length ? e.findings.map(f => `${f.code}: ${f.count} · ${f.action}`).join(' · ') : 'No findings.');
    stage(list, 'Central policy', e.action ?? (payload.error_code === 'evaluation_failed' ? 'Not reached' : 'Not recorded'));
    stage(list, 'Required audit / reporting', 'Durable record found.');
    stage(list, 'Target', `${e.target_id} · model ${e.model_id ?? 'none recorded'} · ${statusLabel(view.invocation_status)}${view.invocation_status === 'unknown' ? ' (missing completion evidence; invocation is not proven)' : ''}`);
    stage(list, 'Measured timing', `Evaluation ${duration(e.evaluation_duration_ms)} · invocation ${duration(view.completion?.invocation_duration_ms)} · total ${duration(view.completion?.total_duration_ms)}`);
  }
  stage(list, 'Immediate outcome', payload.error_code ?? payload.action ?? 'Unavailable');
  $('run-pipeline').replaceChildren(list);
}
async function execute(body, context) {
  if (busy || !loaded || !active) return;
  if (!context.scenario) {
    selected = null;
    $('scenario-selection').replaceChildren();
    document.querySelectorAll('[data-scenario]').forEach(button => {
      button.classList.remove('selected');
      button.setAttribute('aria-pressed', 'false');
    });
  }
  busy = true;
  const token = generation;
  const scenario = context.scenario;
  $('run-result').replaceChildren(); $('run-pipeline').replaceChildren(); $('run-evidence').replaceChildren();
  $('run-context').textContent = scenario ? `Scenario profile: ${scenario.profile} · target local-ollama` : `Application policy · target ${context.target}`;
  const start = Date.now();
  $('run-status').textContent = 'Running · awaiting actual outcome. Pipeline stages pending.';
  elapsedTimer = setInterval(() => { if (token === generation && active) $('run-status').textContent = `Running · ${Math.floor((Date.now() - start) / 1000)}s waiting (browser time). Pipeline stages pending.`; }, 1000);
  updateControls();
  try {
    const { payload } = await interactionPost(body);
    if (token !== generation || !active) return;
    clearInterval(elapsedTimer);
    $('run-status').textContent = payload.error_code ? `Operational outcome: ${payload.error_code}` : `Decision: ${payload.action}`;
    if (scenario) {
      const matches = scenario.expected_error ? payload.error_code === scenario.expected_error : payload.action === scenario.expected_action && scenario.expected_codes.every(c => payload.finding_codes?.includes(c));
      $('run-result').append(element('p', matches ? 'muted' : 'snapshot-note', matches ? 'Observed outcome matches this scenario’s expectation.' : 'Expected / observed mismatch. The actual outcome is shown; enforcement was not overridden.'));
    }
    if (payload.result?.content !== undefined) {
      $('run-result').append(element('h3', '', context.target === 'local-echo' ? 'Approved input returned by Local echo' : 'Uninspected model response'), element('pre', 'output-text', payload.result.content));
    }
    let detail = null;
    if (payload.interaction_id) {
      $('run-result').append(element('p', 'muted', `Interaction ${payload.interaction_id}`));
      try { detail = (await reportingGet(`events/${payload.interaction_id}`)).item; } catch { /* Immediate outcome remains valid when reporting is unavailable. */ }
      if (token !== generation || !active) return;
      if (detail) {
        const button = element('button', 'text-button audit-link', 'Inspect matching audit event'); button.type = 'button';
        button.addEventListener('click', () => {
          const dialog = $('event-dialog'); dialog.dataset.source = 'interactions'; renderEventDetail($('detail-content'), detail); dialog.showModal(); $('close-detail').focus();
        });
        $('run-evidence').append(button);
      }
    }
    pipeline(detail, payload);
    document.dispatchEvent(new Event('interaction-complete'));
  } catch {
    if (token === generation && active) $('run-status').textContent = 'Outcome unknown · connection interrupted. Execution is not retried; the target may still be running.';
  } finally {
    clearInterval(elapsedTimer);
    busy = false;
    if (token !== generation && active) {
      $('run-status').textContent = 'The previous submission’s outcome is unavailable in this view after navigation. Check Security overview for recorded evidence.';
    }
    updateControls();
  }
}
loadWorkspace();
