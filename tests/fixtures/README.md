# Long-lived test fixtures

Compatibility snapshots consumed by tests live under `tests/fixtures/`, independent
of the OpenSpec change lifecycle. Load them relative to the test module rather
than the working directory. Keep historical change evidence in its archive.

`foundation/baseline-http.json` and `foundation/baseline-openapi.json` are byte-for-byte
copies of the pre-extension foundation snapshots captured at commit `97d2c15`.
Their provenance is the archived
[`generalize-control-layer-extension-points` evidence](../../openspec/changes/archive/2026-10-03-generalize-control-layer-extension-points/evidence/).
They preserve the 13 HTTP cases and full OpenAPI document. The schema test permits
only the approved finding-code item broadening; all other assertions remain exact.
Do not regenerate these snapshots from current behavior merely to make tests pass.

The local-model addition normalizes only the `InteractionRequest.target_id`
property from the historical `local-echo` constant to the explicit
`[local-echo, local-ollama]` enum, alongside the previously approved finding-code
broadening. Full OpenAPI equality checks retain all other fields/components,
including the historical `EchoResult` name. Historical JSON remains unchanged.
