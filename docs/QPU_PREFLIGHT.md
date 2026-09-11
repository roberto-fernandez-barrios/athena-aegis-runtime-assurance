# IBM QPU preflight record

Date: 2026-09-11. This is a read-only access audit, not scientific evidence.

## Safe credential search

Searched by variable/configuration names, without reading values into reports:
process, user, and machine environments; PowerShell user environment; Qiskit
saved-account locations; Git-ignored `.env` and local configs; project scripts;
and prior IBM integrations. No credential value or credential-bearing path is
reported. No credential was copied into this repository, examples, logs,
manifests, tests, or CI.

Authentication report after credential replacement:

```text
credential_present = yes
credential_source_type = ignored-env
sdk_version = 0.49.0
channel = ibm_quantum_platform
instance_present = yes
authentication_result = pass
failure_category = none
sanitized_error = none
```

The former ignored-environment credential reached the current channel but did
not resolve a matching accessible instance. The replacement credential
authenticates. Two instances are accessible; their names and CRNs are not
persisted in tracked artifacts. A single physical backend is visible through both entitlements:
`ibm_basquecountry`, operational, 156 qubits, non-simulator, with two pending
jobs at the frozen selection snapshot.

The selected instance CRN and the campaign pseudonym/signing keys exist only in
the local ignored environment. There is no Qiskit saved account. No physical
job or connectivity smoke test has yet been submitted.

## API compatibility

The active environment uses `qiskit-ibm-runtime==0.49.0` with
`qiskit==2.5.2`. Local signature inspection confirmed the installed
`QiskitRuntimeService`, `SamplerV2(mode=...)`, keyword-only `shots`, BackendV2,
and RuntimeJobV2 interfaces. A read-only call exposed Qiskit's `EdgeList` from
`coupling_map.get_edges()`; the adapter now converts that object to canonical
integer pairs before hashing. The preflight never submits jobs and accepts no
token CLI argument.

## Provider metadata snapshot

The frozen least-busy rule leaves one eligible backend and therefore selects
`ibm_basquecountry` before any result exists. At capture time the backend was
active with two pending jobs. Configuration, target, properties, and
calibration data were available. The combined target/configuration projection
has digest `53f3f3923c6fc4c53bb22d46f17d739cf7aa47270bc6f6e5779b7bee286f6ab6`;
calibration timestamp was `2026-09-11T13:14:37+02:00`.

Provider-reported summaries covered 156 T1 values, 156 T2 values, 156 readout
errors, and 1,796 gate-error entries. Queue status was available. Job-level
scheduling timestamps, layout, usage estimation, and session information remain
unavailable until a real job exists. The account API reported 6,000 allocated
seconds, zero consumed, and no reached usage limit at the snapshot.

## Re-entry condition

The read-only gate is satisfied. A physical smoke test is now permitted and
must be registered exactly as **CONNECTIVITY SMOKE TEST — NOT SCIENTIFIC
EVIDENCE**, with one trivial circuit and the minimum compatible shots. Pilot
submission remains prohibited until the smoke result, context, envelope,
manifest, and secret sanitization all pass.
