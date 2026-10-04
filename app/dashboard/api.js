// Shared reporting client. It never sends content or accesses storage.
export async function reportingGet(path, params = {}, signal) {
  const query = new URLSearchParams(params);
  const response = await fetch(`/v1/reporting/${path}${query.size ? `?${query}` : ''}`, {
    signal, cache: 'no-store', headers: { Accept: 'application/json' },
  });
  if (!response.ok) throw new Error('reporting_unavailable');
  return response.json();
}

export async function demoGet(path) {
  const response = await fetch(`/v1/demo/${path}`, { cache: 'no-store', headers: { Accept: 'application/json' } });
  if (!response.ok) { const error = new Error('workspace_unavailable'); error.status = response.status; throw error; }
  return response.json();
}
export async function interactionPost(body) {
  const response = await fetch('/v1/interactions', {
    method: 'POST', cache: 'no-store', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, body: JSON.stringify(body),
  });
  // BLOCK and operational failures are data, not reasons to retry execution.
  return { status: response.status, payload: await response.json() };
}
