# IBM QPU preflight record

Date: 2026-09-11. This was a read-only access audit, not scientific evidence.

## Safe credential search

Searched by variable/configuration names, without reading values into reports:
process, user, and machine environments; PowerShell user environment; Qiskit
saved-account locations; Git-ignored `.env` and local configs; project scripts;
and prior IBM integrations. One relevant credential variable exists in a local
Git-ignored `.env`. It is not tracked. No credential was copied into this
repository, examples, logs, manifests, tests, or CI.

Required report:

```text
credential_found = yes
credential_source_type = ignored-env
authentication_test = fail
```

The sanitized failure was “no matching accessible instance” for the selected
current channel. Consequently instances, backends, status, target,
configuration, properties, calibration, queue, and usage could not be queried.
No physical job or connectivity smoke test was submitted.

## API compatibility

The pre-existing environment used `qiskit-ibm-runtime==0.49.0` and
`qiskit==2.5.1`; the clean project lock verified Runtime 0.49.0 with Qiskit
2.5.2.
`IBMRuntimeAdapter` uses current `QiskitRuntimeService` backend/instance methods,
BackendV2 status/properties/target, and `SamplerV2(mode=backend).run(..., shots=)`.
The preflight never submits jobs and accepts no token CLI argument.

## Re-entry condition

Repair account/instance entitlement or channel selection outside Git. Then run
the zero-cost preflight and save only the sanitized output. A physical smoke
test is permitted only after quota confirmation and must be registered exactly
as **CONNECTIVITY SMOKE TEST — NOT SCIENTIFIC EVIDENCE**, with one trivial
circuit and the minimum compatible shots.
