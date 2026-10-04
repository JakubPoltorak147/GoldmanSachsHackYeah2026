import { reportingGet, usageGet } from './api.js';
import { element, number, duration, timestamp, statusLabel, renderEventDetail } from './detail.js';
import { actionLabel, findingLabel, controlLabel, errorLabel } from './labels.js';

const $ = id => document.getElementById(id);
const filters = $('filters');
const dialog = $('event-dialog');
let generation = 0;
let controller;
let busy = false;
let queued = false;
let selected = null;
let snapshot = null;
let usageSnapshot = null;
let detailSnapshot = null;
let historyPage = null;
let nextCursor = null;
let timer;

function values() {
  return Object.fromEntries(new FormData(filters));
}
function query() {
  const { window: hours, ...filterValues } = values();
  const to = new Date();
  const from = new Date(to.getTime() - Number(hours) * 3600000);
  return { from_time: from.toISOString(), to_time: to.toISOString(), ...Object.fromEntries(Object.entries(filterValues).filter(([, value]) => value)) };
}
function chips() {
  const current = values();
  const nodes = [element('span', 'chip', $('time-window').selectedOptions[0].textContent)];
  for (const [key, value] of Object.entries(current)) {
    if (key !== 'window' && value) nodes.push(element('span', 'chip', key === 'invocation_status' ? statusLabel(value) : value));
  }
  $('filter-chips').replaceChildren(...nodes);
}
function rankings(container, entries, label, count, affected = null) {
  if (!entries.length) {
    container.replaceChildren(element('p', 'muted', 'No findings in this window.'));
    return;
  }
  const sorted = [...entries].sort((a, b) => count(b) - count(a) || label(a).localeCompare(label(b))).slice(0, 5);
  const max = count(sorted[0]);
  container.replaceChildren(...sorted.map(entry => {
    const row = element('div', 'rank-row');
    const caption = element('div', 'rank-caption');
    const title = element('span', 'category', label(entry));
    if (affected) title.append(element('small', '', `${number(affected(entry))} affected interaction${affected(entry) === 1 ? '' : 's'}`));
    caption.append(title, element('strong', '', number(count(entry))));
    const track = element('div', 'bar-track');
    const fill = element('div', `bar-fill${entry.control_id === 'semantic-security' || entry.id === 'semantic-security' ? ' semantic' : ''}`);
    fill.style.width = `${max ? count(entry) / max * 100 : 0}%`;
    track.append(fill);
    row.append(caption, track);
    return row;
  }));
}
function renderSummary(data) {
  const result = data.overall;
  $('metric-total').textContent = number(result.interaction_total);
  for (const action of ['ALLOW', 'REDACT', 'BLOCK']) $('metric-' + action.toLowerCase()).textContent = number(result.actions[action]);
  $('metric-operational').textContent = number(result.operational_failure_total);
  for (const status of ['succeeded', 'failed', 'unknown', 'not_invoked']) $('status-' + status).textContent = number(result.invocations[status]);
  $('findings-deterministic').textContent = number(result.findings.filter(f => f.control_id !== 'semantic-security').reduce((total, f) => total + f.occurrences, 0));
  $('findings-semantic').textContent = number(result.findings.filter(f => f.control_id === 'semantic-security').reduce((total, f) => total + f.occurrences, 0));
  rankings($('finding-rankings'), result.findings, f => findingLabel(f.code), f => f.occurrences, f => f.affected_interactions);
  const controls = new Map();
  for (const finding of result.findings) controls.set(finding.control_id, (controls.get(finding.control_id) ?? 0) + finding.occurrences);
  rankings($('control-rankings'), [...controls].map(([id, count]) => ({ id, count })), f => controlLabel(f.id), f => f.count);
  $('timing-stats').replaceChildren(...[['evaluation', 'Evaluation'], ['semantic', 'Semantic evaluator'], ['invocation', 'Target invocation'], ['total', 'Total to completion']].map(([key, title]) => {
    const timing = result[key];
    const row = element('div', 'timing-row');
    const name = element('span', '', title);
    name.append(element('small', '', `${number(timing.samples)} recorded sample${timing.samples === 1 ? '' : 's'}`));
    const value = element('span', 'timing-value');
    value.append(element('strong', '', timing.mean_ms === null ? '—' : timing.mean_ms.toFixed(2)));
    if (timing.samples) value.append(element('small', '', `min ${timing.min_ms.toFixed(2)} · max ${timing.max_ms.toFixed(2)}`));
    row.append(name, value);
    return row;
  }));
  $('health-label').textContent = data.reporting_health === 'healthy' ? 'Write-gate health: healthy' : 'Write-gate health: reporting_write_failed';
  $('health-label').style.color = data.reporting_health === 'healthy' ? '' : 'var(--amber)';
  $('window-label').textContent = `Evidence window: ${timestamp(data.window.from_time)} – ${timestamp(data.window.to_time)}`;
}
function meter(title, counter, unit) {
  const ratio = counter.limit ? counter.used / counter.limit : 0;
  const state = counter.used >= counter.limit ? 'over' : ratio >= 0.8 ? 'near' : 'ok';
  const row = element('div', `usage-meter ${state}`);
  const caption = element('div', 'rank-caption');
  caption.append(
    element('span', 'category', title),
    element('strong', '', `${number(counter.used)} of ${number(counter.limit)} ${unit}`),
  );
  const track = element('div', 'bar-track');
  track.setAttribute('role', 'meter');
  track.setAttribute('aria-label', title);
  track.setAttribute('aria-valuemin', '0');
  track.setAttribute('aria-valuemax', String(counter.limit));
  track.setAttribute('aria-valuenow', String(Math.min(counter.used, counter.limit)));
  const fill = element('div', 'bar-fill');
  fill.style.width = `${Math.min(100, ratio * 100)}%`;
  track.append(fill);
  const remaining = Math.max(0, counter.limit - counter.used);
  const note = state === 'over' ? 'Limit reached' : state === 'near' ? 'Near limit' : 'Within budget';
  row.append(caption, track, element('small', 'usage-note', `${note} · ${number(remaining)} ${unit} remaining`));
  return row;
}
function renderUsage(usage, stale = false) {
  const body = $('usage-body');
  const state = $('usage-state');
  state.classList.toggle('stale', stale);
  if (!usage) {
    state.textContent = 'Unavailable';
    body.replaceChildren(element('p', 'muted', 'Usage data unavailable. No budget state is inferred.'));
    return;
  }
  if (!usage.enabled) {
    state.textContent = 'Disabled';
    body.replaceChildren(element('p', 'muted', 'The usage budget control is disabled in the active policy, so requests are not metered.'));
    return;
  }
  state.textContent = stale ? 'Stale · last successful read' : `Resets in ${number(usage.resets_in_seconds)}s`;
  const facts = element('div', 'usage-facts');
  const breaches = usage.breaches;
  for (const [label, value] of [
    ['Window', `${number(usage.window_seconds)} s`],
    ['Per-request limit', `${number(usage.max_request_tokens)} est. tokens`],
    ['Breaches since start', `${number(breaches.request_limit)} request · ${number(breaches.token_limit)} token · ${number(breaches.request_size)} size`],
  ]) {
    const item = element('span', '', label);
    item.append(element('strong', '', value));
    facts.append(item);
  }
  body.replaceChildren(
    meter('Requests in window', usage.requests, 'requests'),
    meter('Estimated tokens in window', usage.estimated_tokens, 'tokens'),
    facts,
  );
}
function renderEvents(data) {
  const focusId = document.activeElement?.dataset?.interaction;
  $('event-count').textContent = number(data.items.length);
  $('event-empty').hidden = data.items.length !== 0;
  $('event-rows').replaceChildren(...data.items.map(view => {
    const event = view.event;
    const row = element('tr');
    const action = element('td');
    action.append(element('span', `pill ${(event.action ?? 'operational').toLowerCase()}`, actionLabel(event.action)), element('small', 'event-id', event.interaction_id.slice(0, 8)));
    const target = element('td', '', event.target_id);
    target.append(element('small', '', event.model_id ?? 'No model identity'));
    const findings = element('td', 'event-findings', event.findings.length ? event.findings.map(f => findingLabel(f.code)).join(', ') : event.error_code ? errorLabel(event.error_code) : 'No findings');
    const status = element('td', 'event-invocation');
    status.append(element('span', `status-dot ${view.invocation_status}`), element('span', '', statusLabel(view.invocation_status)));
    if (view.invocation_status === 'unknown') status.title = 'No durable completion; invocation is not proven';
    const latency = element('td', '', duration(event.evaluation_duration_ms));
    const time = element('td', '', timestamp(event.timestamp));
    const detail = element('td');
    const button = element('button', 'detail-button', 'View →');
    button.type = 'button';
    button.dataset.interaction = event.interaction_id;
    button.setAttribute('aria-label', `View event ${event.interaction_id.slice(0, 8)}`);
    button.addEventListener('click', () => openDetail(event.interaction_id));
    detail.append(button);
    row.append(action, target, findings, status, latency, time, detail);
    return row;
  }));
  nextCursor = data.next_before_sequence;
  $('older-events').disabled = nextCursor === null;
  $('back-live').hidden = historyPage === null;
  $('page-label').textContent = historyPage === null ? 'Latest events · refreshed every 3 seconds' : 'Older page · select Back to live events to follow updates';
  if (focusId && !dialog.open) [...document.querySelectorAll('[data-interaction]')].find(n => n.dataset.interaction === focusId)?.focus();
}
function targets(data) {
  const select = $('target');
  const known = new Set([...select.options].map(option => option.value));
  for (const view of data.items) {
    const id = view.event.target_id;
    if (!known.has(id)) {
      const option = element('option', '', id);
      option.value = id;
      select.append(option);
      known.add(id);
    }
  }
}
function availability(message, stale = false) {
  $('availability').textContent = message;
  $('availability').classList.toggle('stale', stale);
}
function invalidate() {
  generation += 1;
  controller?.abort();
  historyPage = null;
  chips();
  availability(snapshot ? 'Updating filters… previous evidence remains visible until refresh.' : 'Loading security evidence…', Boolean(snapshot));
  refresh();
}
function schedule() {
  clearTimeout(timer);
  if (!document.hidden && !$('overview-view').hidden) timer = setTimeout(refresh, 3000);
}
async function refresh() {
  clearTimeout(timer);
  if (document.hidden || $('overview-view').hidden) return;
  if (busy) { queued = true; return; }
  busy = true;
  const token = generation;
  const id = selected;
  const params = query();
  controller = new AbortController();
  const signal = controller.signal;
  $('refresh').disabled = true;
  try {
    const results = await Promise.allSettled([
      reportingGet('summary', params, signal),
      reportingGet('events', { ...params, limit: '50' }, signal),
      usageGet(signal),
      ...(id ? [reportingGet(`events/${id}`, {}, signal)] : []),
    ]);
    if (token !== generation) return;
    if (results[2].status === 'fulfilled') {
      usageSnapshot = results[2].value;
      renderUsage(usageSnapshot);
    } else {
      renderUsage(usageSnapshot, true);
    }
    if (results[0].status === 'fulfilled' && results[1].status === 'fulfilled') {
      snapshot = { summary: results[0].value, events: results[1].value, params };
      renderSummary(snapshot.summary);
      targets(snapshot.events);
      if (historyPage === null) renderEvents(snapshot.events);
      $('last-updated').textContent = `Updated ${timestamp(snapshot.summary.generated_at)}`;
      availability(snapshot.summary.reporting_health === 'healthy' ? 'Live evidence · read-only · all metrics reflect the selected window.' : 'Reporting write gate is unhealthy. Existing evidence remains readable; new dispatch is closed.', snapshot.summary.reporting_health !== 'healthy');
    } else {
      availability(snapshot ? 'Reporting unavailable · displayed evidence is stale. Last successful update is shown below.' : 'Reporting unavailable · no evidence loaded. Retrying in 3 seconds.', true);
    }
    if (id && id === selected && dialog.open) {
      if (results[3].status === 'fulfilled') {
        detailSnapshot = { id, view: results[3].value.item };
        renderEventDetail($('detail-content'), detailSnapshot.view);
      } else {
        if (detailSnapshot?.id === id) renderEventDetail($('detail-content'), detailSnapshot.view);
        else $('detail-content').replaceChildren();
        $('detail-content').prepend(element('p', 'snapshot-note', 'Event detail unavailable. Any displayed detail is stale; no new outcome is inferred.'));
      }
    }
  } catch (error) {
    if (token === generation && error.name !== 'AbortError') availability('Reporting unavailable. No new evidence inferred.', true);
  } finally {
    busy = false;
    $('refresh').disabled = false;
    if (queued || token !== generation) { queued = false; refresh(); }
    else schedule();
  }
}
function openDetail(id) {
  selected = id;
  detailSnapshot = null;
  $('detail-content').replaceChildren(element('p', 'detail-error', 'Loading safe event detail…'));
  dialog.showModal();
  $('close-detail').focus();
  generation += 1;
  controller?.abort();
  refresh();
}
function closeDetail() { dialog.close(); }
dialog.addEventListener('close', () => {
  if (dialog.dataset.source === 'interactions') {
    delete dialog.dataset.source;
    document.querySelector('.audit-link')?.focus();
    return;
  }
  const id = selected;
  selected = null;
  detailSnapshot = null;
  const trigger = [...document.querySelectorAll('[data-interaction]')].find(node => node.dataset.interaction === id);
  (trigger ?? $('events-heading')).focus();
});
$('close-detail').addEventListener('click', closeDetail);
filters.addEventListener('submit', event => event.preventDefault());
filters.addEventListener('change', invalidate);
$('clear-filters').addEventListener('click', () => { filters.reset(); invalidate(); });
$('refresh').addEventListener('click', refresh);
$('back-live').addEventListener('click', () => { historyPage = null; if (snapshot) renderEvents(snapshot.events); refresh(); });
$('older-events').addEventListener('click', async () => {
  if (!snapshot || nextCursor === null || busy) return;
  const token = generation;
  const cursor = nextCursor;
  busy = true;
  clearTimeout(timer);
  controller = new AbortController();
  $('older-events').disabled = true;
  try {
    const page = await reportingGet('events', { ...snapshot.params, limit: '50', before_sequence: String(cursor) }, controller.signal);
    if (token !== generation) return;
    historyPage = page;
    targets(page);
    renderEvents(page);
    // Pagination is separate from the live first-page cache.
  } catch (error) {
    if (token === generation && error.name !== 'AbortError') availability('Older events unavailable · retained evidence is stale.', true);
  } finally {
    busy = false;
    if (token === generation) $('older-events').disabled = nextCursor === null;
    if (queued || token !== generation) { queued = false; refresh(); }
    else schedule();
  }
});
document.addEventListener('visibilitychange', () => {
  $('live-label').lastChild.textContent = document.hidden ? ' Paused while hidden' : ' Polling · 3s';
  if (document.hidden) clearTimeout(timer);
  else refresh();
});
document.addEventListener('console-view', () => {
  generation += 1;
  controller?.abort();
  clearTimeout(timer);
  if (!$('overview-view').hidden) refresh();
});
document.addEventListener('interaction-complete', refresh);
chips();
refresh();
