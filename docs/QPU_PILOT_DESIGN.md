# QPU pilot design v1

Status: designed, not run. The pilot is separate from the confirmatory campaign
and is not evidence for headline hypotheses.

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
