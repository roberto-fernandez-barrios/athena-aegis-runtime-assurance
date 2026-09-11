# Preregistration v1 — DRAFT, NOT FROZEN

Study: Context-conditioned longitudinal assurance for hybrid quantum-classical
services under non-stationary QPU execution.

Draft date: 2026-09-11. This document is incomplete by design because the
zero-cost IBM preflight has not produced an accessible instance/backend and the
non-confirmatory pilot has not been run. No confirmatory QPU experiment may be
submitted until all `[PILOT-FIX]` fields are resolved, analysis/config hashes are
recorded, this file is committed, and the freeze commit/tag is registered.
A connectivity smoke test is explicitly not scientific evidence.

## 1. Research questions

RQ1: Can observable execution context determine when a previously calibrated
assurance rule remains valid under longitudinal QPU non-stationarity?

RQ2: Does explicit pre-decision OOS/context abstention reduce unsafe
continuation relative to context-agnostic calibration, at what false-hold cost?

RQ3: Which declared rerun/recalibrate/fallback/rollback action restores service
correctness after invalid assurance or hold, and at what latency, resource, and
availability cost?

RQ4: Does the mechanism transfer between the Paper-1.5 kernel regression and a
small routing workload, and instantiate the AEGIS slice of HSaaS/FMS without
claiming global WP5 validation?

## 2. Primary hypotheses

- H1: Predeclared context-support scores discriminate supported from held-out
  OOS execution units above chance, with sensitivity/specificity targets fixed
  after pilot and before confirmation `[PILOT-FIX]`.
- H2: P4 yields lower unsafe continuation than P2 on paired post-shift units.
  The primary estimand is the paired absolute risk difference P4 minus P2.
- H3: P5 yields greater independently verified service correctness after an
  invalid/held execution than P4 alone, subject to increased latency/resource
  use reported rather than hidden.
- H4: Authenticated item/prediction/label binding reduces accepted corrupted
  tuples versus no binding, with false-rejection and runtime/storage overhead
  jointly reported.

No directional headline hypothesis is registered for a second backend or full
FMS QAOA until the pilot establishes feasibility. Calibration coverage is not
claimed outside frozen support premises.

## 3. Primary endpoints

Definitions, denominators, experimental units, aggregation, and uncertainty are
normative in `configs/metrics.v1.json`:

1. unsafe continuation rate (primary policy endpoint);
2. false hold rate (co-primary safety/availability trade-off);
3. context OOS detection;
4. calibration validity violation;
5. recovery success rate;
6. fallback correctness;
7. time to recovery;
8. service availability;
9. decision error after context shift.

Secondary resource endpoints are QPU jobs, shots, wall-clock, observable queue
time, reruns, recalibrations, classical overhead, and evidence storage overhead.
Recovery completion without independent correctness does not count as success.

## 4. Population, units, and dependence

Calibration population: repeated executions of the frozen logical workload in
the frozen supported backend/configuration/context strata during calibration
windows `[PILOT-FIX]`.

Calibration unit: one independently assigned workload service request (or one
predeclared batch aggregate if provider batching makes requests inseparable)
within a temporal window `[PILOT-FIX]`.

Test unit: one service request assigned to one policy/context intervention.
The QPU job is a resource unit, not automatically an independent statistical
unit. Circuits sharing a job, calibration snapshot, or temporal window are
clustered and never treated as independent repetitions.

Exchangeability premise: within a frozen supported context stratum/window,
calibration/test nonconformity scores are assumed exchangeable conditional on
the declared context and randomization. Temporal windows are not assumed
exchangeable without sensitivity analysis. Outside support, state is
`CONTEXT_OOS`; after expiry/update failure, state is `CALIBRATION_INVALID`.

## 5. Backend selection and physical evidence

Primary backend rule: among accessible, operational, non-simulator backends
fitting the workload, choose the least pending-jobs backend at the frozen
selection timestamp using only provider-visible status. Tie break
lexicographically by backend ID. Record all candidates and missing status. The
selected backend, instance scope, qubit requirements, and permitted failover are
`[PILOT-FIX]`.

One backend with a complete causal chain is primary. A second backend is added
only if quota remains after physical interventions, multiple temporal windows,
one closed workload, and recovery evaluation. Simulator runs never substitute
for physical evidence.

## 6. Workloads and reference correctness

Primary: `paper15-kernel-regression-v1`, independently packaged
compute-uncompute ZZ-feature-map fidelity kernel, with exact statevector kernel
reference. Instance/dataset, feature scaling, repetitions, sample count,
semantic hash, shots, and correctness threshold are `[PILOT-FIX]`.

Secondary: the AEGIS slice of the FMS demonstrator, a small closed-route
instance with an exact brute-force classical oracle. The instance and QUBO/QAOA
encoding are included only if the pilot freezes a feasible circuit; otherwise
the classical oracle and quantum handoff remain an integration result, not a
confirmatory quantum-workload claim. No global WP5 claim is permitted.

## 7. Policies and actions

Arms are P0 serve always, P1 log only, P2 global calibrated, P3
context-conditioned, P4 context-conditioned plus OOS abstention, and P5 P4 plus
recovery/enforcement. The pilot may remove P1 or P3 if empirically and
mechanistically redundant; P0, P2, P4, and P5 remain necessary contrasts.

Action semantics are frozen in `docs/POLICIES_AND_ACTIONS.md`. Policy is
evaluated on the same captured evidence where counterfactual replay is valid;
live actions use randomized/paired assignment `[PILOT-FIX]`. No result served
under insufficient evidence is called fail-closed.

## 8. Context support and calibration

Candidate support baselines are exact declared strata, standardized distance,
and diagonal-Gaussian relative density. Candidate fields are backend/version,
shots, optimization/runtime options, layout/qubit subset, calibration age,
T1/T2/readout/gate summaries, target digest, and provider-visible queue/context.
Unavailable fields are never imputed silently.

Pilot selection uses leave-one-context/window-out discrimination and stability,
not confirmatory endpoint optimization. Frozen model, fields, normalization,
threshold, tie handling, missingness rule, and reference windows are
`[PILOT-FIX]`. OOS evaluation occurs before a calibrated rule. Exact strata are
the default if the pilot cannot defend a continuous model.

Calibration specification to freeze: population, unit, conditional
exchangeability premise, temporal window/expiry, context stratum, test unit,
alpha `[PILOT-FIX]`, quantile rule, update triggers, minimum sample size
`[PILOT-FIX]`, and recalibration rule. Split-conformal/empirical quantiles, if
used, are methodological components, not novelty. Nominal alpha language is
prohibited for OOS/invalid states.

## 9. Temporal windows and assignment

The number of windows is derived after the pilot from observed within/between
context variability, the desired uncertainty width for P4 minus P2, QPU cost,
backend availability, and feasible cadence. Required values—window count,
cadence/tolerance, requests per cell, and target interval width—are
`[PILOT-FIX]`.

Multiple separated windows are mandatory. With fewer than three usable
temporal windows, between-window variance is not estimated reliably and the
longitudinal claim is killed. Natural drift is observed; it is not manufactured
or causally attributed. Within windows, instance/intervention/policy order is
seeded and randomized or counterbalanced. Seed and assignment digest are
`[PILOT-FIX]`.

## 10. Controlled interventions

Use only the A--H declarations in `configs/interventions.v1.json`: benign
context variation, natural calibration drift, client-visible configuration
change, seeded accidental local fault, bounded malicious local substitution,
held-out feasible OOS context, provider-visible scheduling/context observation,
and recovery action. Realized levels/budgets are `[PILOT-FIX]`.

No experiment claims the ability to modify IBM calibration, internal queue,
hardware, telemetry, other tenants, or provider trust roots. Authenticated
binding evaluation assumes the adversary cannot read/write the local key.

## 11. Recovery rules

Default order for P5 `[PILOT-FIX after feasibility]`: binding failure -> BLOCK
or FALLBACK; unsupported/expired calibration -> RECALIBRATE or FALLBACK;
supported semantic failure -> one RERUN; failed rerun -> FALLBACK; invalid
new release with a valid frozen predecessor -> ROLLBACK; otherwise HOLD.

Maximum reruns, recalibration sample cost, service deadline, fallback quality
criterion, rollback eligibility, and terminal hold duration are
`[PILOT-FIX]`. All actions and failed actions remain in the denominator.

## 12. Statistical analysis

- Estimate every rate with numerator/denominator counts and Wilson 95% CI.
- Primary P4-versus-P2 unsafe-continuation comparison: paired risk difference
  with a temporal-window-cluster bootstrap CI; an exact paired test is a
  sensitivity analysis when counts permit.
- Estimate OOS sensitivity and supported-context specificity. AUROC is reported
  only for a frozen continuous score and with window-cluster bootstrap CI.
- Time to recovery: median and empirical survival/censoring summary by strategy,
  with cluster-bootstrap CI.
- Quality/cost outcomes: paired within-instance contrasts aggregated first
  within window, then across windows. Jobs/circuits in one provider batch do not
  inflate sample size.
- Calibration validity: report empirical violation by support class/window;
  compare with alpha only where every frozen premise holds.
- Report all policies/interventions/windows, including negative and failed
  cells. Multiplicity: H2 is the single primary confirmatory contrast; H1/H3/H4
  are ordered secondary hypotheses `[PILOT-FIX if power supports hierarchy]`.

Analysis code and builder versions/hashes are `[FREEZE-FIX]`. No headline number
may be typed manually into the manuscript.

## 13. Exclusions and missingness

Exclude before outcome inspection only: duplicate registry ID; schema-invalid
or digest-invalid envelope; provider-cancelled job demonstrably unrelated to
assigned workload; predeclared maintenance outage; or experimenter error that
occurred before QPU execution. Exclusions remain logged and counted in resource
and reliability summaries. Timeout, queue failure, calibration absence, context
missingness, recovery failure, and invalid/OOS decisions are outcomes, not
convenient exclusions. No post-hoc outlier removal.

If a context field is unavailable, mark unavailable and follow the frozen
missingness rule. Complete-case deletion is not default. Backend retirement or
API change triggers an amendment before further confirmatory jobs.

## 14. Kill criteria

- KC1 no physical QPU evidence: no physical-execution-assurance claim.
- KC2 insufficient windows/temporal variation: no longitudinal claim.
- KC3 support model fails to separate supported/OOS contexts at the frozen
  pilot threshold: reduce to context diagnostics.
- KC4 recovery does not improve unsafe continuation/service correctness: publish
  the negative result and limit enforcement claim.
- KC5 metadata/confidentiality endpoints not measurable: move that analysis to
  the project technical report.
- KC6 FMS slice cannot be coordinated or physically implemented: retain an
  explicitly named workload proxy and make no WP5/global-demonstrator claim.

Additional operational kill: unresolvable credential/entitlement, unaffordable
quota, or backend feasibility failure means no campaign and activates KC1. Kills
are reported, not hidden.

## 15. Expected outcomes and falsification

Expected, not assumed: P4 lowers unsafe continuation versus P2 but raises false
holds; P5 restores correctness/availability at resource/latency cost; exact
strata or a simple distance baseline is sufficient; binding blocks local tuple
substitution with small classical overhead. Evidence against these expectations
is publishable. The strongest claim is falsified if context support does not
predict calibration validity or if abstention/recovery fails to improve the
declared service endpoint.

## 16. Freeze checklist

- [ ] Successful sanitized IBM preflight and backend/usage observability.
- [ ] Separate connectivity smoke (optional) labelled non-scientific.
- [ ] Pilot registry complete; pilot data excluded from confirmation.
- [ ] All `[PILOT-FIX]` and `[FREEZE-FIX]` placeholders resolved.
- [ ] Window precision/cost derivation attached.
- [ ] Backend/workload/policy/intervention/randomization hashes recorded.
- [ ] Analysis builders tested and hashed.
- [ ] Secret scan and full test suite pass.
- [ ] This preregistration committed and tagged before confirmatory submission.
