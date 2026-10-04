import { demoGet, interactionPost, reportingGet } from './api.js';
import { element, duration, statusLabel, renderEventDetail } from './detail.js';
import { actionLabel, findingLabel, findingMeaning, controlLabel, errorLabel } from './labels.js';

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
  document.querySelectorAll('[data-scenario]').forEach(button => { button.disabled = busy || !loaded; });
  if ($('run-scenario')) $('run-scenario').disabled = busy || !loaded || !selected?.enabled;
}
function targetDescription() {
  const target = metadata?.custom.targets.find(t => t.target_id === $('custom-target').value);
  $('target-description').textContent = target?.target_id === 'local-echo' ? 'Returns approved input after the checks. No generation call; enabled semantic controls still run.' : target ? `Generates from approved input. Configured model: ${target.model_id ?? 'not recorded'}. Availability is determined when you run.` : 'No registered public target available.';
}
$('custom-content').addEventListener('input', updateControls);
$('custom-target').addEventListener('change', targetDescription);

function clearResult() {
  clearInterval(elapsedTimer);
  $('run-context').textContent = initialResult;
  $('run-status').textContent = 'No interaction submitted.';
  $('run-result').replaceChildren();
  $('run-explanation').replaceChildren();
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
  $('run-context').textContent = `${scenario.title} · Prepared scenario`;
  const description = element('p', '', scenario.description);
  const expected = element('p', '', `Expected: ${scenario.expected_error ? errorLabel(scenario.expected_error) : actionLabel(scenario.expected_action)}`);
  const run = element('button', 'button primary', 'Run scenario'); run.type = 'button'; run.id = 'run-scenario';
  run.addEventListener('click', () => execute({ scenario_id: scenario.id }, { scenario, target: 'local-ollama' }));
  $('scenario-selection').append(element('h3', '', 'What this tests'), description, expected, element('p', '', scenario.expected_explanation));
  $('scenario-selection').append(element('p', scenario.simulation ? 'simulation-label' : 'muted', scenario.simulation ? 'Controlled unavailable-transport simulation' : 'Synthetic example · fixed server profile'));
  const requirements = scenario.runtime_requirements;
  const runtimeText = requirements.includes('semantic') ? 'Needs the configured semantic evaluator. If classification permits forwarding, the configured generation model may also be called.' : requirements.includes('generation') ? 'Needs the configured local generation model to complete the response.' : scenario.simulation ? 'No available model runtime is required for this isolated transport-failure simulation.' : 'Expected BLOCK needs no model runtime: the target is not called. If actual policy allows forwarding, the configured model is still used.';
  $('scenario-selection').append(element('h3', '', 'Before you run'), element('p', 'muted', runtimeText));
  if (scenario.prerequisite) $('scenario-selection').append(element('p', 'muted', scenario.prerequisite));
  const technical = element('details', 'technical-detail');
  technical.append(element('summary', '', 'Technical expectation'), element('p', 'muted', `Profile: ${scenario.profile}`), element('p', 'muted', scenario.expected_codes.map(findingLabel).join(' · ') || 'No security finding expected.'));
  $('scenario-selection').append(technical);
  $('scenario-selection').append(run);
  document.querySelectorAll('[data-scenario]').forEach(button => (button.classList.toggle('selected', button.dataset.scenario === scenario.id), button.setAttribute('aria-pressed', String(button.dataset.scenario === scenario.id))));
  updateControls();
  if (matchMedia('(max-width: 700px)').matches) $('result-heading').focus();
}
function renderCatalog() {
  const nodes = [];
  for (const category of ['Benign', 'Deterministic', 'Semantic', 'Failure modes']) {
    nodes.push(element('h3', '', category));
    for (const scenario of catalog.filter(s => s.category === category)) {
      const button = element('button', 'scenario-item'); button.type = 'button'; button.dataset.scenario = scenario.id; button.setAttribute('aria-pressed', 'false');
      button.append(element('strong', '', scenario.title), element('small', '', scenario.enabled ? `Expected: ${scenario.expected_error ? errorLabel(scenario.expected_error) : actionLabel(scenario.expected_action)}` : `Execution disabled · ${scenario.prerequisite}`));
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
  $('custom-guidance').textContent = 'Current checks are unavailable until configuration loads.';
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
    const row = element('div', 'control-row'); row.append(element('span', '', controlLabel(control.control_id)), element('span', '', control.enabled ? 'Enabled' : 'Disabled')); $('custom-controls').append(row);
  }
  const semantic = metadata.custom.controls.find(c => c.control_id === 'semantic-security');
  $('custom-guidance').textContent = semantic ? `Semantic inspection is ${semantic.enabled ? 'enabled' : 'disabled'} for custom input under the application policy.${semantic.enabled ? ' Even Local echo requires the configured evaluator.' : ' Local echo needs no model runtime under this policy.'} Enabling semantic scenario cards does not enable custom inspection. Changing the target does not change this policy.` : 'The current semantic setting is unavailable. Changing the target does not select a scenario policy.';
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
    stage(list, 'Deterministic controls', e.control_status.filter(([id]) => id !== 'semantic-security').map(([id, enabled]) => `${controlLabel(id)}: ${!enabled ? 'disabled' : e.evaluated_controls.includes(id) ? 'completed' : 'not completed'}`).join(' · '));
    const semanticEnabled = e.control_status.some(([id, enabled]) => id === 'semantic-security' && enabled);
    stage(list, 'Semantic evaluator', `${e.semantic_status ?? (semanticEnabled ? 'Not attempted / not recorded' : 'Disabled')} · evaluator ${e.semantic_model_id ?? 'not recorded'} · ${duration(e.semantic_duration_ms)}`);
    stage(list, 'Findings', e.action === null ? 'Partial findings not recorded for operational failure.' : e.findings.length ? e.findings.map(f => `${findingLabel(f.code)}: ${f.count} · ${actionLabel(f.action)}`).join(' · ') : 'No findings.');
    stage(list, 'Central policy', e.action ? actionLabel(e.action) : payload.error_code === 'evaluation_failed' ? 'Not reached' : 'Not recorded');
    stage(list, 'Required audit / reporting', 'Durable record found.');
    stage(list, 'Target', `${e.target_id} · model ${e.model_id ?? 'none recorded'} · ${statusLabel(view.invocation_status)}${view.invocation_status === 'unknown' ? ' (missing completion evidence; invocation is not proven)' : ''}`);
    stage(list, 'Measured timing', `Evaluation ${duration(e.evaluation_duration_ms)} · invocation ${duration(view.completion?.invocation_duration_ms)} · total ${duration(view.completion?.total_duration_ms)}`);
  }
  stage(list, 'Immediate outcome', payload.error_code ? errorLabel(payload.error_code) : payload.action ? actionLabel(payload.action) : 'Unavailable');
  $('run-pipeline').replaceChildren(list);
}

function explain(view, payload) {
  const recorded = view?.event;
  const action = payload.action ?? recorded?.action;
  const error = payload.error_code;
  let happened;
  let why;
  let next;
  if (error) {
    happened = errorLabel(error);
    const explanations = {
      evaluation_failed: ['A safety check could not finish. There is no policy decision and nothing was sent to the target.', 'Ask the operator to check the configured evaluator and runtime. The error alone does not identify a specific cause.'],
      audit_failed: ['Required auditing failed. The target was not invoked; no durable record is assumed.', 'Ask the operator to check audit and reporting health before another explicit submission.'],
      target_failed: ['The target failed after the request became eligible for dispatch. Eligibility and successful execution are separate.', 'Ask the operator to check the configured generation runtime and model. This request is not retried or sent to another target.'],
      invalid_request: ['The gateway rejected the request. No security finding or completed check is inferred.', 'Check the input and workspace configuration before choosing another explicit submission.'],
    };
    [why, next] = Object.hasOwn(explanations, error) ? explanations[error] : ['The request could not be completed by the service. Unrecorded checks and outcomes are unavailable.', 'Check service and workspace availability. Execution is not retried automatically.'];
    if (error === 'evaluation_failed' && recorded?.semantic_status === 'failed') why += ' The matching event records a failed semantic evaluation attempt.';
    if (error === 'target_failed') why += recorded?.action ? ` Recorded policy decision: ${actionLabel(recorded.action)}.` : ' The earlier policy decision is unavailable in reporting.';
  } else {
    happened = actionLabel(action);
    why = action === 'BLOCK' ? 'Central policy stopped the request. The target was not invoked.' : action === 'REDACT' ? 'Policy selected redaction before eligible forwarding. The target receives only approved text.' : 'The configured checks allowed the input. ALLOW is not a guarantee of safety; target completion is separate.';
    next = action === 'BLOCK' ? 'Remove the described sensitive or attack-shaped material before choosing a new explicit submission.' : 'Read the labelled echo or model response if present, and inspect the recorded checks. Model output is uninspected.';
  }
  const nodes = [element('h3', '', 'What happened'), element('p', '', happened), element('h3', '', 'Why'), element('p', '', why)];
  if (recorded?.action && recorded.findings.length) {
    const findings = element('ul', 'finding-reasons');
    for (const f of recorded.findings) {
      const row = element('li');
      row.append(element('strong', '', findingLabel(f.code)), element('p', '', findingMeaning(f.code)), element('small', 'muted', `${f.count} recorded occurrence${f.count === 1 ? '' : 's'} · ${controlLabel(f.control_id)} · mapped to ${actionLabel(f.action)}`));
      findings.append(row);
    }
    nodes.push(findings);
  } else if (!view) {
    if (payload.finding_codes?.length) nodes.push(element('p', '', `Immediate finding codes: ${payload.finding_codes.map(findingLabel).join(' · ')}`));
    nodes.push(element('p', 'muted', 'Recorded finding counts, mapped actions, audit persistence and target completion are unavailable.'));
  } else if (!error) nodes.push(element('p', 'muted', recorded.action ? 'No findings were recorded.' : 'No policy decision or findings were recorded.'));
  if (view) nodes.push(element('p', 'muted', `Recorded target outcome: ${statusLabel(view.invocation_status)}.${view.invocation_status === 'unknown' ? ' Missing completion evidence; this does not prove invocation.' : ''}`));
  nodes.push(element('h3', '', 'What happens next'), element('p', '', next));
  $('run-explanation').replaceChildren(...nodes);
}

function comparison(scenario, payload, view) {
  const panel = element('section', 'expectation-comparison');
  panel.append(element('h3', '', 'Expected vs observed'), element('p', '', `Expected: ${scenario.expected_error ? errorLabel(scenario.expected_error) : actionLabel(scenario.expected_action)}`), element('p', '', `Observed: ${payload.error_code ? errorLabel(payload.error_code) : actionLabel(payload.action)}`));
  let message;
  let matches = false;
  if (!view || view.invocation_status === 'unknown') {
    message = 'Cannot verify full expectation: recorded pipeline or completion evidence is unavailable. The immediate response remains visible.';
  } else {
    const e = view.event;
    if (scenario.expected_error === 'evaluation_failed') {
      matches = payload.error_code === scenario.expected_error && e.error_code === scenario.expected_error && e.action === null && e.semantic_status === 'failed' && view.invocation_status === 'not_invoked';
    } else if (scenario.expected_error === 'target_failed') {
      matches = payload.error_code === scenario.expected_error && e.action === scenario.expected_action && view.invocation_status === 'failed' && view.completion?.error_code === 'target_failed';
    } else {
      matches = !payload.error_code && payload.action === scenario.expected_action && e.action === scenario.expected_action && scenario.expected_codes.every(c => payload.finding_codes?.includes(c) && e.findings.some(f => f.code === c)) && (scenario.expected_action === 'BLOCK' ? view.invocation_status === 'not_invoked' : view.invocation_status === 'succeeded' && typeof payload.result?.content === 'string') && (scenario.profile !== 'semantic-live' || e.semantic_status === 'succeeded');
    }
    message = matches ? 'Observed outcome matches this scenario’s expectation, including recorded execution status.' : `Expected / observed mismatch.${e.action === scenario.expected_action && view.invocation_status === 'failed' && !scenario.expected_error ? ' The policy action matches, but target execution failed.' : ''} The actual outcome is shown; enforcement was not overridden.`;
    panel.append(element('p', 'muted', `Recorded policy: ${actionLabel(e.action)} · target: ${statusLabel(view.invocation_status)}${e.semantic_status ? ` · evaluator: ${statusLabel(e.semantic_status)}` : ''}`));
  }
  panel.append(element('p', matches ? 'muted' : 'snapshot-note', message));
  $('run-result').prepend(panel);
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
  $('run-result').replaceChildren(); $('run-explanation').replaceChildren(); $('run-pipeline').replaceChildren(); $('run-evidence').replaceChildren();
  $('run-context').textContent = scenario ? `${scenario.title} · Prepared scenario · Local model` : `Custom interaction · Application policy · ${context.target === 'local-echo' ? 'Local echo' : 'Local model'}`;
  const start = Date.now();
  $('run-status').textContent = 'Running · awaiting actual outcome. Pipeline stages pending.';
  elapsedTimer = setInterval(() => { if (token === generation && active) $('run-status').textContent = `Running · ${Math.floor((Date.now() - start) / 1000)}s waiting (browser time). Pipeline stages pending.`; }, 1000);
  updateControls();
  try {
    const { payload } = await interactionPost(body);
    if (token !== generation || !active) return;
    clearInterval(elapsedTimer);
    $('run-status').textContent = payload.error_code ? errorLabel(payload.error_code) : actionLabel(payload.action);
    if (payload.result?.content !== undefined) {
      $('run-result').append(element('h3', '', context.target === 'local-echo' ? 'Approved input returned by Local echo' : 'Uninspected model response'), element('pre', 'output-text', payload.result.content));
    }
    let detail = null;
    if (payload.interaction_id) {
      $('run-result').append(element('p', 'muted', `Interaction ${payload.interaction_id}`));
      try {
        const item = (await reportingGet(`events/${payload.interaction_id}`)).item;
        if (item.event.interaction_id === payload.interaction_id) detail = item;
      } catch { /* Immediate outcome remains valid when reporting is unavailable. */ }
      if (token !== generation || !active) return;
      if (detail) {
        const button = element('button', 'text-button audit-link', 'Inspect matching audit event'); button.type = 'button';
        button.addEventListener('click', () => {
          const dialog = $('event-dialog'); dialog.dataset.source = 'interactions'; renderEventDetail($('detail-content'), detail); dialog.showModal(); $('close-detail').focus();
        });
        $('run-evidence').append(button);
      }
    }
    explain(detail, payload);
    if (scenario) comparison(scenario, payload, detail);
    pipeline(detail, payload);
    document.dispatchEvent(new Event('interaction-complete'));
  } catch {
    if (token === generation && active) {
      $('run-status').textContent = 'Outcome unknown · connection interrupted. Execution is not retried; the target may still be running.';
      $('run-explanation').replaceChildren(element('h3', '', 'What happened'), element('p', '', 'The connection ended before an outcome could be confirmed.'), element('h3', '', 'What happens next'), element('p', '', 'Check Security overview for available evidence. The target may still be running; no retry or cancellation is assumed.'));
    }
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
