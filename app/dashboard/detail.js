import { actionLabel, controlLabel, findingLabel, findingMeaning, errorLabel } from './labels.js';

// All reporting values are inserted as text, including administrative identities.
export function element(tag, className = '', text = null) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== null) node.textContent = String(text);
  return node;
}
export const number = value => new Intl.NumberFormat().format(value);
export const duration = value => value === null || value === undefined ? '—' : `${value.toFixed(2)} ms`;
export const timestamp = value => new Date(value).toLocaleString([], {
  month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit',
});
export const statusLabel = value => ({ succeeded: 'Succeeded', failed: 'Failed', unknown: 'Unknown', not_invoked: 'Not invoked' })[value] ?? 'Unavailable';
function section(title) {
  const node = element('section', 'detail-section');
  node.append(element('h3', '', title));
  return node;
}
function details(parent, pairs) {
  const list = element('dl', 'detail-grid');
  for (const [label, value] of pairs) list.append(element('dt', '', label), element('dd', '', value ?? 'Not recorded'));
  parent.append(list);
}
export function renderEventDetail(container, view) {
  const event = view.event;
  const summary = section('Decision & identity');
  details(summary, [
    ['Interaction ID', event.interaction_id], ['Recorded at', timestamp(event.timestamp)],
    ['Decision', actionLabel(event.action)], ['Event type', event.event_type],
    ['Reason / error', event.error_code ? errorLabel(event.error_code) : event.reason_code === 'no_findings' ? 'No findings from configured checks (no_findings)' : event.reason_code === 'policy_resolved' ? 'Policy resolved the recorded findings (policy_resolved)' : 'Not recorded'],
    ['Target', event.target_id], ['Target model', event.model_id],
    ['Invocation', statusLabel(view.invocation_status)], ['Target error', view.completion?.error_code ? errorLabel(view.completion.error_code) : 'None recorded'],
  ]);
  if (view.invocation_status === 'unknown') summary.append(element('p', 'muted', 'Eligible decision with no durable completion. This does not prove the target was invoked.'));
  const controls = section('Controls & security findings');
  for (const [id, enabled] of event.control_status) {
    const row = element('div', 'detail-control');
    row.append(element('span', '', controlLabel(id)), element('span', '', !enabled ? 'Disabled' : event.evaluated_controls.includes(id) ? 'Evaluated' : 'Not completed'));
    controls.append(row);
  }
  if (!event.findings.length) controls.append(element('p', 'muted', event.action === null ? 'No findings recorded for operational failures.' : 'No security findings.'));
  for (const finding of event.findings) {
    const row = element('div', 'detail-finding', findingLabel(finding.code));
    row.append(element('p', '', findingMeaning(finding.code)), element('small', '', `${controlLabel(finding.control_id)} · ${number(finding.count)} occurrence${finding.count === 1 ? '' : 's'} · mapped to ${actionLabel(finding.action)}`));
    controls.append(row);
  }
  const semantic = section('Semantic evaluator');
  const semanticEnabled = event.control_status.some(([id, enabled]) => id === 'semantic-security' && enabled);
  details(semantic, [['Evaluator model', event.semantic_model_id], ['Attempt status', event.semantic_status ?? (semanticEnabled ? 'Not recorded / not attempted' : 'Disabled')], ['Semantic duration', duration(event.semantic_duration_ms)]]);
  const timings = section('Measured timings');
  details(timings, [['Evaluation', duration(event.evaluation_duration_ms)], ['Target invocation', duration(view.completion?.invocation_duration_ms)], ['Total to completion', duration(view.completion?.total_duration_ms)]]);
  timings.append(element('p', 'muted', 'Evaluation excludes audit and target invocation. Semantic timing is included in evaluation. No per-control timings are recorded.'));
  const audit = section('Required reporting evidence');
  details(audit, [['Policy digest', event.policy_digest], ['Forwarding eligible', event.forwarding_eligible ? 'Yes' : 'No'], ['Event sequence', view.sequence], ['Schema version', view.schema_version], ['Completion recorded', view.completion ? timestamp(view.completion.completed_at) : 'No completion record']]);
  container.replaceChildren(summary, controls, semantic, timings, audit);
}
