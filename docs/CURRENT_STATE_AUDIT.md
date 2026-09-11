# Paper 2.5 current-state audit

Audit date: 2026-09-11. Scope: local workspace `rf`; read-only inspection of
Paper 1.5 and project sources. No Paper 1.5 file, tag, release, or history was
modified.

## Authoritative sources read in full

1. `hybrid-quantum-classical-integrity/Proyecto/ATHENA-Memoria.pdf` (32 pages).
2. `hybrid-quantum-classical-integrity/Proyecto/PLAN_ATHENA_AEGIS_DEUSTO_ABSOLUTE_CEILING.md`
   (1,525 lines).

The project memory defines HSaaS as a hybrid service path and gives an FMS
routing example in which an orchestrator selects classical or external quantum
execution. WP3 assigns AEGIS the secure/reliable hybrid-computation slice:
design, transpilation/scheduling/post-processing, QPU execution,
integrity/confidentiality, end-to-end V&V, metrics, threats, and enforcement.
WP5 is the global FMS demonstrator and involves consortium-wide coordination.
Accordingly, this repository implements only the **AEGIS slice of the FMS
demonstrator** and does not claim WP5 validation.

The ceiling plan's latest scientific correction supersedes its earlier fixed
window ambition: the number and cadence of temporal windows must follow a
pilot, observed variability, desired precision, interval width, QPU cost, and
backend availability. The retained causal chain is context -> calibration
validity -> OOS decision -> physical execution -> enforcement -> recovery ->
service consequence.

## Existing implementation

No coherent, isolated Paper 2.5 repository existed. Paper 2.5 appeared as a
future-work boundary in Paper 1.5 documents and source, not as an executable
project. This new repository was therefore created separately.

Paper 1.5 is clean at local `main` HEAD `88f19b1`; scientific/editorial tag
`paper15-q1-v1.3.8` resolves to `6d57056`. Reused concepts were read from its
policy, contract, QSVC, statevector-kernel, schema, and test code. No code is
imported by path: the regression workload is independently packaged here.

Relevant companion repositories found locally:

- `Tesis/qevc`: conditional validity of quantum event classifiers; physical
  micro-QPU artifacts on `ibm_marrakesh`, but not a Paper 2.5 longitudinal
  campaign.
- `Tesis/target_domain_certificates`: target-domain quantum-kernel
  certificates under distribution shift.
- `Tesis/validate-before-commit`: model-promotion/deployment validation gate.

These constrain positioning; none is treated as Paper 2.5 data.

## QPU credential and SDK audit

Security result (values were never printed, copied, logged, or committed):

| Check | Result |
|---|---|
| credential_found | yes |
| credential_source_type | ignored-env |
| authentication_test | pass |

The replacement value is persisted only in a Git-ignored local environment;
its value is never emitted. Instance selection and local pseudonym/signing keys
are also ignored. The tracked-file scan found no embedded IBM credential. One
separately labelled connectivity smoke job has completed; it is not scientific
evidence and is excluded from confirmation.

The active repository environment contains Python 3.11, Qiskit 2.5.2 and
qiskit-ibm-runtime 0.49.0. The IBM adapter targets the locally inspected API
(`QiskitRuntimeService`, `SamplerV2`, BackendV2 and RuntimeJobV2). Read-only
authentication now exposes two entitlements and one eligible physical backend.
Status, target/configuration digest, properties, calibration, queue and safe
numeric usage limits are captured in the sanitized preflight artifact. The real
Qiskit 2.5.2 `EdgeList` response revealed and motivated one canonicalization
fix. The connectivity smoke passed submit/result/context/envelope validation;
the non-confirmatory pilot is the only live execution now permitted.

## Evidence gap at repository creation

Prior companion artifacts prove earlier IBM connectivity but lack the repeated,
Paper-2.5-specific context snapshots, pre-declared support decisions, policy
actions, recovery outcomes, and service endpoints required here. Therefore:

- `physical_qpu_evidence = absent` for Paper 2.5;
- `longitudinal_windows = 0`;
- `provider_attestation = absent`;
- the confirmatory campaign is prohibited until preregistration is frozen.

## Implemented response

This repository now owns the execution/evidence schemas, provider boundary,
simulator, kernel regression workload, FMS oracle/skeleton, support baselines,
P0--P5 policies, enforcement and recovery interfaces, authenticated evaluation
binding, confidentiality minimization, metric/intervention registries, pilot
protocol, tests, and CI. IBM Runtime remains optional and replaceable behind
`ProviderAdapter`.

## Current live status after the audit

The authenticated read-only preflight selected one physical backend by the
pre-result least-busy rule. One 32-shot connectivity smoke and the four
pre-execution-amended pilot jobs completed successfully. These five jobs are
all `phase=pilot`, `scientific_evidence=false`; confirmatory jobs remain zero.

The pilot used one calibration epoch, so repeated-execution variability is
observable but longitudinal variability is not. The result, candidate
3/5/8/10-window budgets, provisional context-support assessment and KC1--KC6
status are recorded in `docs/QPU_PILOT_RESULT.md`. Confirmatory preregistration
remains draft and no campaign is authorized.
