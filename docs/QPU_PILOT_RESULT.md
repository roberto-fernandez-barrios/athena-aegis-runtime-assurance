# QPU pilot result

Date: 2026-09-11. Phase: `pilot`. Scientific evidence: `false`.

This report describes the four jobs fixed in `QPU_PILOT_DESIGN.md`. It makes no
inference about RQ1--RQ4, does not freeze the confirmatory preregistration, and
does not promote pilot executions into `artifacts/confirmatory/`.

## Executed jobs

All jobs used `ibm_basquecountry`, six two-qubit circuits, optimization level 1,
the fixed three-sample input, and the exact statevector oracle.

| Job | Block | Shots | Seed | Created (UTC) | Running (UTC) | Finished (UTC) | Queue s | Wall s | QPU charge s | Result |
|---:|---:|---:|---:|---|---|---|---:|---:|---:|---|
| 1 | 1 | 128 | 19062026 | 12:06:47.566 | 12:06:50.237 | 12:06:59.629 | 2.671 | 13.344 | 2 | DONE |
| 2 | 1 | 512 | 19062026 | 12:07:02.253 | 12:07:03.850 | 12:07:12.288 | 1.596 | 11.063 | 3 | DONE |
| 3 | 2 | 128 | 19062027 | 12:07:14.749 | 12:07:15.872 | 12:07:23.719 | 1.123 | 10.469 | 2 | DONE |
| 4 | 2 | 512 | 19062027 | 12:07:26.498 | 12:07:27.612 | 12:07:35.581 | 1.114 | 10.375 | 3 | DONE |

Observation: 4/4 jobs succeeded without rerun. Mean provider-reported queue
time was 1.626 s (range 1.114--2.671); mean local wall clock was 11.313 s. Pilot
charge was 10 provider-account seconds; usage estimation summed to 12.234
quantum seconds. Monetary cost was not exposed and is therefore unavailable.

## 1. Can the workload execute reliably?

- **Observation:** all four jobs returned six normalized count maps, and every
  map summed to its requested shots. Layout was `[0,1]` for all circuits.
- **Inference:** connectivity and short-workload execution were reliable in
  this single availability interval.
- **Design decision:** kernel feasibility passes; this is not a scientific
  reliability estimate for a longitudinal campaign.

## 2. Which context fields are available?

- **Observation:** 32/37 ExecutionContext fields were available in every pilot
  job. Backend/configuration version, calibration timestamp, T1/T2, readout and
  gate-error summaries, target/configuration digest, queue, layout/qubits,
  transpilation controls/hash, Runtime primitive/version, workload identities,
  provider timestamps and usage were captured.
- **Observation:** session ID, resilience options, dynamical-decoupling options,
  measurement-mitigation options and observable definition were unavailable.
- **Inference:** the implemented total-context schema matches the live payload;
  missing values must remain explicit rather than reconstructed.

## 3. What is the metadata missingness?

- **Observation:** missingness was 5/37 = 13.51% in each pilot job. The same five
  fields were missing in all four records.
- **Observation:** one completed job retained provider-reported usage status
  `pending` while the authoritative Runtime job status was `DONE`; this field is
  therefore preserved as untrusted provider evidence, not harmonized post hoc.
- **Inference:** the kernel path has sufficient metadata for local provenance,
  calibration snapshot comparison and usage accounting, but no Runtime session
  evidence or mitigation/DD evidence exists for this design.
- **Design decision:** those fields remain `unavailable`; no surrogate values
  are introduced.

## 4. What QPU variability is observed?

| Shots | Mean oracle relative Frobenius error | Worst absolute error | Repeat relative Frobenius discrepancy | Repeat max discrepancy |
|---:|---:|---:|---:|---:|
| 128 | 0.05738 | 0.06058 | 0.07562 | 0.08594 |
| 512 | 0.02993 | 0.04030 | 0.04660 | 0.05078 |

- **Observation:** 512 shots reduced both oracle error and repeated-execution
  discrepancy in this pilot.
- **Inference:** this is within-epoch repeated-execution variability. All four
  contexts share calibration timestamp `2026-09-11T13:14:37+02:00`; no
  between-calibration or longitudinal variability was observed.

## 5. Which shot count is defensible?

- **Observation:** 128 and 512 both satisfy the threshold fixed before QPU
  execution. The rule selects the smallest passing level.
- **Design decision:** recommend 128 shots for the current two-qubit/six-circuit
  kernel workload. This minimizes charge while satisfying the pilot criterion;
  it is not a confirmatory threshold and does not generalize to FMS/QAOA.

## 6. What does a job cost?

- **Observation:** 128-shot jobs charged 2 account seconds and reported 2.551
  estimated quantum seconds; 512-shot jobs charged 3 seconds and reported
  3.566. Local wall times were 10.375--13.344 s across all jobs.
- **Inference:** a conservative planning allowance is 3 QPU seconds per
  128-shot kernel job. Monetary cost and contractual billing units are
  unavailable.

## 7. Does the queue permit a longitudinal campaign?

- **Observation:** all pilot jobs entered running status within 2.671 s and the
  account retained 5,988/6,000 seconds after smoke plus pilot.
- **Inference:** queue and quota permit this small workload under the observed
  interval. A one-minute pilot cannot establish future queue availability.
- **Design decision:** queue is not a kill criterion now, but every future
  window must repeat the read-only quota/status gate.

## 8. What cadence is viable?

- **Observation:** only one calibration epoch was observed; IBM exposed its
  timestamp but not a guaranteed future calibration schedule.
- **Design decision:** use event-driven cadence: read-only polling and one
  acquisition window per distinct provider calibration timestamp. Calendar
  spacing remains unresolved until a calibration turnover is observed.

## 9. How many windows are defensible?

Assumption for planning only: two independent 128-shot jobs per window. The
precision column is the worst-case binomial 95% shot-only half-width per
circuit. It ignores QPU drift, within-window dependence, policy contrasts and
between-window variance, so it cannot by itself size RQ1--RQ4.

| Candidate windows | Shot-only precision | Kernel jobs | Conservative QPU budget | Acquisition wall time under pilot queue | Calendar duration | Statistical/feasibility interpretation |
|---:|---:|---:|---:|---:|---|---|
| 3 | ±3.54 pp | 6 | 18 s | 71 s | ≥2 unknown calibration intervals | Minimum for a variance estimate; too unstable to recommend |
| 5 | ±2.74 pp | 10 | 30 s | 119 s | ≥4 unknown calibration intervals | Computationally feasible; misses proposed 2.5 pp shot-only target |
| 8 | ±2.17 pp | 16 | 48 s | 191 s | ≥7 unknown calibration intervals | Smallest candidate meeting proposed shot-only target |
| 10 | ±1.94 pp | 20 | 60 s | 238 s | ≥9 unknown calibration intervals | Precision reserve if calendar duration remains feasible |

- **Design decision:** do not freeze a window count. Retain 8 as the primary
  feasibility candidate and 10 as the precision reserve, subject to author
  approval, observed calibration cadence and confirmatory endpoint sizing.

## 10. Is more than one backend required?

- **Observation:** exactly one physical backend was accessible and it completed
  the workload.
- **Inference:** a second backend is unnecessary for infrastructure validation.
- **Design decision:** retain one backend for the initial longitudinal design;
  do not introduce a second-backend campaign unless a real failure or editor
  requirement changes the scope.

## 11. Which ContextSupportModel can be preregistered?

| Model | Interpretability | Pilot fit stability | OOS separability | Recommendation |
|---|---|---|---|---|
| Exact strata | High | Stable for the observed backend/target epoch | Unmeasured beyond one epoch | Conservative provisional candidate |
| Standardized distance | Medium/high | Unstable: four contexts and near-zero between-context variance | Not estimable | Retain candidate; do not freeze |
| Diagonal Gaussian density | Medium | Insufficient sample and degenerate variance | Not estimable | Retain candidate; do not freeze |

- **Design decision:** no model is frozen. Exact strata is the provisional
  conservative choice because it abstains on unseen strata without estimating a
  density from four same-epoch contexts. Distance and Gaussian remain candidates
  until genuinely distinct contexts exist.

## 12. Are any kill criteria activated?

- **KC1:** feasibility not triggered: five real QPU jobs exist (one smoke, four
  pilot). Scientific physical-QPU assurance remains unclaimed because all five
  are non-confirmatory.
- **KC2:** active for any present longitudinal claim: only one calibration epoch
  and zero independent longitudinal windows exist.
- **KC3:** unresolved: no supported-versus-OOS context separation can be tested.
- **KC4:** unresolved scientifically; simulator/infrastructure transitions for
  HOLD, RERUN, RECALIBRATE, FALLBACK, ROLLBACK and BLOCK all produced verifiable
  envelopes.
- **KC5:** not triggered for pilot feasibility: the metadata endpoint is
  measurable with explicit 13.51% missingness.
- **KC6:** unresolved and out of this pilot: FMS/QAOA was not submitted.

## Integrity correction and stop boundary

Post-run verification found that QPY serialization changed across identical
local transpile calls despite identical seed and layout. Counts, QPU outputs,
oracle metrics and provider timestamps were unaffected. Before committing the
pilot, transpiled identity was corrected to a deterministic OpenQASM-2-plus-
final-layout projection; regression tests prove repeatability. The affected
derived context values were recomputed and envelopes locally re-sealed without
submitting another QPU job.

The pilot is closed. `PREREGISTRATION_v1.md` remains `DRAFT, NOT FROZEN`.
No confirmatory campaign may start until the author reviews this report, the
window/job-budget recommendation and the actual context metadata.
