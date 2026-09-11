# Operational threat and intervention model v1

## Protected outcome and trust boundary

The protected outcome is the correctness and declared availability of an
HSaaS result when quantum execution is used. Trusted roots are the local AEGIS
policy code, frozen configuration/schema versions, classical reference/oracle,
local key custody, and append-only experiment registry. IBM-reported properties,
queue/status, job metadata, and results are inputs from an untrusted external
boundary unless a future cryptographic provider mechanism is independently
verified. Current IBM evidence is provider-reported evidence, not attestation.

The client, AEGIS service, classical orchestrator, provider, auditor, and
artifact consumer are separate principals. Provider-internal scheduling,
calibration operations, tenant isolation, and hardware control are not locally
writable and cannot be assigned as experimental attacker powers.

## Integrity and operational failures in scope

- stale calibration applied to a shifted execution context;
- backend, layout/transpilation, shots, or runtime-option shift;
- observable queue/scheduling/context change;
- natural physical drift between temporal windows;
- accidental corruption or misalignment of item/prediction/label tuples;
- controlled malicious tampering within local write sets;
- invalid continuation after unsupported evidence;
- incorrect or failed rerun, recal recal, fallback, rollback, or hold.

Out of scope for causal attack claims: arbitrary modification of IBM hardware,
fabricated provider telemetry, provider signing keys, internal queue placement,
other tenants, or confidential provider control planes. These remain blind
regions inherited from the Paper 1.5 epistemic boundary.

## Intervention taxonomy

The authoritative machine-readable declarations are in
`configs/interventions.v1.json`. Every realized intervention must freeze actor,
capability, write set, read set, knowledge, objective, budget, trusted roots,
and expected consequence before execution.

| Class | Meaning | Controllable example |
|---|---|---|
| A | benign context variation | seed/layout or shot-count variation within declared support |
| B | natural calibration drift | separated snapshot/window; observed, not injected |
| C | configuration change | optimization/resilience option changed by orchestrator |
| D | accidental fault | seeded result truncation or tuple permutation |
| E | malicious integrity intervention | bounded local label/prediction substitution |
| F | OOS context | held-out backend family or out-of-range declared stratum |
| G | provider-visible scheduling/context | observed pending jobs/session mode; no queue control claim |
| H | recovery action | rerun, recalibrate, fallback, rollback, or hold |

## Authenticated binding countermeasure

Before aggregation, the service MAC-binds `evaluation_id`, `item_id`, prediction,
and evaluation label. It can prevent/detect unauthorized local tuple
substitution under uncompromised key custody. It does not authenticate a label's
truth, protect after key compromise, or constitute novel cryptography. Endpoints
are corruption prevented, false rejection, fallback triggered, recovery
correctness, and overhead.

## Decision safety

`ALLOW` serves the candidate. `HOLD` withholds pending review/action. `BLOCK`
permanently rejects that request under the current policy. Recovery actions are
not successful until the independently checked output meets the frozen service
criterion. The term fail-closed is permitted only when no candidate result is
served under insufficient evidence.
