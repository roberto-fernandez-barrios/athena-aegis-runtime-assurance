# Research questions and claims v1

Status: pilot-facing freeze candidate, not confirmatory freeze.

## RQ1 — Context validity

Can observable execution context determine when a previously calibrated
assurance rule remains valid under longitudinal QPU non-stationarity?

Primary contrast: supported versus OOS executions, labelled by a held-out
controlled context intervention or pre-declared temporal/context stratum. The
claim is predictive discrimination and validity diagnosis, not causal
attribution of provider-internal physics.

## RQ2 — Abstention

Does explicit pre-decision context/OOS abstention reduce unsafe continuation
relative to a context-agnostic calibrated rule, and what false-hold cost does it
incur?

Primary contrast: P4 versus P2 on paired/randomized workload instances within
temporal windows. The calibrated assurance claim is made only for supported
contexts satisfying the frozen assumptions; OOS execution enters
`CONTEXT_OOS`, not a nominal alpha guarantee.

## RQ3 — Recovery

When calibration is invalid or an execution is held, which pre-declared
rerun/recalibrate/classical-fallback/rollback action restores service
correctness, and at what availability, latency, QPU, and classical cost?

Primary contrast: P5 versus P4 and P0. Recovery success requires an independently
verified service result; merely executing an action is not success.

## RQ4 — Transfer and ATHENA

Does the mechanism retain useful discrimination and service benefit across the
Paper-1.5 kernel regression workload and the AEGIS routing slice, and does its
event/evidence flow instantiate the AEGIS portion of an HSaaS/FMS workflow?

Transfer is bounded to frozen workloads/backends. It is not a claim of global
FMS/WP5 validation or arbitrary-QPU generalization.

## Exact retained contribution

The non-overlapping claim sought is that a service can operationalize
calibration support as an execution-time precondition, abstain before invalid
evidence becomes assurance, enforce a recovery action, and quantify downstream
correctness/availability consequences across repeated physical-QPU contexts.
Contracts, hashes, false-alarm calibration, local allow/hold decisions, generic
provenance, conformal prediction per se, and blind-region arguments are
infrastructure or baselines, not novelty claims.
