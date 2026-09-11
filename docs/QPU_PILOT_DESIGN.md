# QPU pilot design v1

Status: executed exactly as pre-execution amended on 2026-09-11. The pilot is
closed, separate from the confirmatory campaign, and not evidence for headline
hypotheses. No design parameter was changed after observing the results.

## Purpose

Estimate job reliability, shot/resource cost, observable context variability,
backend availability, exposed runtime/job metadata, kernel workload size, and a
defensible temporal-window cadence/count. The pilot selects among exact strata,
standardized distance, and diagonal-Gaussian density; it must not optimize a
confirmatory effect estimate.

## Backend and workload

Use one accessible operational non-simulator backend with sufficient qubits for
the three-sample Paper-1.5 kernel regression workload. Select by a frozen
least-busy rule using only accessible provider status; record all eligible
backends and the selection time. Do not add a second backend unless the first
causal chain is closed and budget remains.

Initial factors are two shot levels (128, 512) and two deterministic transpiler
seeds at optimization level 1. At most four physical pilot jobs follow a
separate connectivity smoke test. Begin with two temporally separated
observations; their separation is chosen after provider calibration cadence and
queue availability are visible.

## Pre-execution amendment — 2026-09-11

The live Runtime 0.49/Qiskit 2.5.2 API and selected backend support the planned
SamplerV2 workload. The previously unspecified three-sample input is now fixed,
before any QPU result, to `(0.1,0.2)`, `(0.3,0.4)`, `(0.5,0.6)`. It produces six
two-qubit compute-uncompute circuits. The separate smoke test is fixed to one
Hadamard-plus-measurement circuit, 32 shots, and optimization level 0.

The four pilot jobs are ordered `(128,19062026)`, `(512,19062026)`,
`(128,19062027)`, `(512,19062027)`. The first two form observation block 1;
block 2 begins only after block 1 completes and a fresh read-only context
snapshot is taken. IBM exposes a calibration timestamp but not a guaranteed
future calibration cadence. Consequently, if both blocks share a calibration
epoch, the pilot estimates repeated-execution variability only and makes no
longitudinal-variation claim. This is a clarification of technical execution,
not a post-result redesign.

The exact-statevector comparisons are relative Frobenius error, mean absolute
error, and maximum absolute error. Same-shot repeats use the corresponding
Frobenius, mean-absolute, and maximum-absolute discrepancies. Select the
smallest shot level whose mean relative Frobenius error is at most 0.15, maximum
absolute error at most 0.20, and repeat relative Frobenius discrepancy at most
0.15; otherwise leave the shot count unresolved. These thresholds are pilot
feasibility criteria, not confirmatory acceptance thresholds.

## Captures and estimates

Before submission and after result retrieval, capture backend status/target,
properties timestamp and summaries, available queue/session metadata, runtime
options, logical/transpiled hashes, selected layout/qubits, job timestamps,
shots, raw/postprocessed digests, success/failure, queue time when exposed,
wall-clock, and kernel correctness against the exact statevector reference.
Unknown fields remain explicitly unavailable.

Estimate:

- job completion probability and failure taxonomy;
- shot-level kernel error and interval width;
- between-snapshot versus within-snapshot context variation;
- support-baseline score distributions on leave-one-context/window-out splits;
- jobs/shots/QPU seconds and elapsed time per service unit;
- missingness of every requested provider field.

## Window derivation rule

The confirmatory window count is not hard-coded. Simulate/resample pilot window
effects and choose the smallest feasible count whose uncertainty target for the
primary P4-versus-P2 unsafe-continuation contrast is declared and met, subject
to quota and availability. At least two separated windows are required to call
the study repeated; fewer than three independent temporal windows cannot
support a stable between-window variance estimate and therefore kills the
longitudinal claim. If the pilot has too little shift to size that contrast, use
precision for OOS sensitivity and predeclare controlled feasible context
interventions rather than manufacturing drift.

## Stop/kill rules

Stop without QPU submission when authentication/quota is unavailable, the
backend cannot fit the workload, private identifiers cannot be pseudonymized,
or estimated use exceeds the approved cap. Stop the pilot if more than half of
jobs fail for non-workload reasons. Do not promote pilot executions into the
confirmatory dataset.
