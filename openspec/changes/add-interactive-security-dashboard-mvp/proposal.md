# Proposal

## Why

The durable reporting foundation already records useful, privacy-safe security evidence, but challenge judges cannot inspect it interactively. A polished read-only dashboard makes existing controls and real local-model integration visible with minimal new backend work.

## What Changes

- Serve a responsive dashboard from the existing FastAPI application using local HTML, CSS and small JavaScript modules.
- Add three read-only versioned reporting routes for summary, newest-first events and safe detail, delegating to the typed reporting store.
- Add only the bounded newest-first typed query needed to show recent events without scanning history.
- Show interaction/action totals, operational evaluation failures, all invocation statuses, deterministic/semantic finding rankings, trusted identities and available timing samples.
- Poll every three seconds; provide filters, event selection and clear empty/loading/stale/error states.
- Keep all reporting content-free and preserve interaction schemas, central enforcement and required audit gates.

Out of scope: scenario execution (the second change), authentication platforms, analytics frameworks, WebSockets, budgets, output inspection, policy editing/reload, retention/export and backend restructuring.

## Capabilities

### New Capabilities

- `security-dashboard`: Read-only operator UI and polling behavior over safe reporting evidence.

### Modified Capabilities

- `security-reporting`: Permit a small HTTP query boundary and add bounded newest-first listing while preserving existing typed queries and privacy guarantees.

## Impact

Own new `app/dashboard/` assets and `app/control_layer/reporting_api.py`; make small composition changes in `api.py` and one additive query in `reporting_store.py`. Add focused unit/integration and essential Playwright journey coverage. No database migration, model dependency, frontend build system or frontend framework is required. Document implemented behavior only during apply.

Independent of the workbench: ship and verify this change first. It defines reusable versioned reporting DTOs, event UUID links, detail renderer and a dashboard navigation/content slot; it contains no executable demo route or demo placeholder requiring change 2.
