// Shared reporting client. It never sends content or accesses storage.
export async function reportingGet(path, params = {}, signal) {
  const query = new URLSearchParams(params);
  const response = await fetch(`/v1/reporting/${path}${query.size ? `?${query}` : ''}`, {
    signal, cache: 'no-store', headers: { Accept: 'application/json' },
  });
  if (!response.ok) throw new Error('reporting_unavailable');
  return response.json();
}
