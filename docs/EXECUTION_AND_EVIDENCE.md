# Execution context and evidence envelope

## ExecutionContext v1

`ExecutionContext` is total: every schema field is present even when its value
is unavailable. Each value carries both an origin and trust class:

- `locally_observed` / `trusted_local` for local clocks, configs, hashes, and
  pseudonyms;
- `provider_reported` / `untrusted` for IBM properties, status, queue, job, or
  calibration data;
- `derived` / `trusted_local` only when derived exclusively from trusted local
  material;
- `derived` / `untrusted` when any source is provider-reported;
- `unavailable` / `unavailable` with a reason instead of a fabricated value.

The schema captures provider/backend identity, time, pseudonymized job/session,
shots, qubits/layout, transpiler controls and versions, runtime primitive and
options, mitigation/DD/resilience settings, provider calibration timestamp,
T1/T2/readout/gate summaries, target digest, observable queue/scheduling
metadata, workload/circuit/transpiled identity, environment/dataset/model
digests, and calibration window.

Field presence is not a trust claim. IBM status/properties can be locally
captured and locally integrity-protected while remaining provider-reported.
`schemas/execution-context.v1.schema.json` is the normative serialization
schema.

## EvidenceEnvelope v1

The envelope binds execution context, request/workload identity, semantic and
transpiled identities, provider-reported evidence, raw and postprocessed result
digests, authenticated evaluation bindings, decision, enforcement, recovery,
and parent provenance digests. Canonical JSON uses recursively sorted keys and
compact UTF-8 encoding; the envelope is sealed with SHA-256.

An optional `Signer` authenticates the local capture boundary. The bundled HMAC
implementation is an interface/reference implementation, not public-key
non-repudiation. It guarantees integrity only from local capture onward under
local-key security. It does not prove that provider metadata is truthful and is
never called provider attestation.

Circuit semantic hashes are stable structural identifiers under the declared
serializer. They do not prove semantic equivalence. The transpiled identity is
separate because a stable logical workload may map to different physical
executions.
