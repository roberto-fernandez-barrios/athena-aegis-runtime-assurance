# Preregistration v1 — FROZEN — CONFIRMATORY DESIGN

Study: Context-aware abstention and enforced recovery for longitudinal runtime
assurance of a hybrid quantum-classical service.

Design date: 2026-09-11. Freeze timestamp: `2026-09-14T09:03:33Z`. The instance
audit, connectivity smoke, non-confirmatory pilot, and infrastructure review are
complete. They are not confirmatory scientific evidence. This document and the
eight machine-readable configs are frozen by the annotated tag
`paper25-prereg-v1`. The exact freeze commit is the commit dereferenced by that
tag. `submission_authorized=true` means only that a later agent may begin the
strict runbook gates; `campaign_started=false`, and this freeze executed no
provider or QPU job.

## 1. Final claim and research questions

The claim to be tested, not assumed, is: context-aware abstention followed by
enforced recovery can reduce unsafe continuation relative to context-agnostic
stale calibration while recovering useful service across genuine provider
calibration transitions. For H1, "unsafe continuation" means the oracle-based
`unsafe_service_continuation` endpoint defined in Section 11; assurance-invalid
continuation is separate and secondary.

- RQ1: Does context-aware abstention followed by enforced recovery reduce
  unsafe continuation relative to context-agnostic calibration while recovering
  useful service?
- RQ2: What service completion, recovery success, false-hold, recovery-latency,
  fallback-correctness, and resource consequences accompany that contrast?
- RQ3: Under which genuine provider calibration transitions does stale
  context-agnostic assurance lose declared validity or service correctness?
- RQ4: Does a fixed optimization-level controlled OOS stress show compatible
behavior without replacing the longitudinal result?

## 2. Hypothesis hierarchy

- H1, primary: P5 reduces unsafe service continuation relative to P2 across
  accepted physical-QPU calibration-context transitions. The estimand is the
  mean across usable windows of within-window paired `RD_service,w =
  unsafe_service_continuation(P5) - unsafe_service_continuation(P2)`. The
  expected beneficial direction is negative, but no negative effect is assumed.
- H2, secondary: P5 restores service after OOS abstention with measurable
  recovery success and availability.
- H3, secondary: stale context-agnostic calibration exhibits
  calibration-validity degradation under at least some genuine calibration
  transitions.
- H4, exploratory/transfer: the predeclared controlled configuration OOS
  stress, and only in later future work an FMS workload, shows compatible
  behavior.

H1 is the only primary hypothesis. If H1 is not supported, H2 or H3 will not be
promoted to rescue the headline claim. Negative P5 results are reported without
changing the contrast, endpoint, perturbation, or hierarchy.

## 3. Fixed campaign scope

- `pilot_instance` and `confirmatory_instance` remain separate. The real CRNs,
  credentials, and pseudonymization keys exist only in ignored local state.
- Every live adapter requires explicit `instance_role=confirmatory`; missing or
  ambiguous mappings block before provider access. There is no silent instance,
  backend, policy, or fallback selection.
- Primary backend: `ibm_basquecountry`; exactly one backend, with no
  cross-backend failover.
- Primary workload: unchanged `paper15-kernel-regression-v1`, three fixed
  samples, six two-qubit compute-uncompute circuits, 128 shots.
- Target: 10 accepted workload-relevant calibration windows. At least 8 usable
  windows are required for a longitudinal claim.
- `PhaseBudgetGuard` runs before every submit. Context polling is read-only.
- Paper 1.5 is not modified. FMS/QAOA is outside this campaign and cannot be
  invoked to replace a weak confirmatory result.

## 4. Statistical units and dependence

The top-level longitudinal unit is one accepted, usable calibration window.
`W` is therefore 8–10 for longitudinal inference. A calibration job is one
separately submitted execution/service unit under the same frozen context
snapshot. A service probe is a request nested in that window. The 39 calibration
units, six pre-recovery probes, two verification probes, circuits, and shots do
not create additional longitudinal epochs or inflate `W`.

Strict physical independence of the 39 calibration jobs is not claimed.
Provider scheduling, drift within an otherwise unchanged observable snapshot,
and shared hardware can induce within-window dependence. Submit-start,
provider-accept, result, and local-observation order are retained. The exact
finite-sample calibration statement is conditional on the declared within-window
exchangeability assumption: within one frozen exact stratum, the 39 calibration
nonconformity scores and an eligible test score are exchangeable conditional on
the declared context and pre-outcome randomization. No exchangeability premise
is extended across provider calibration epochs.

Ten windows are an operational replication target, not a formal power result or
a claim of statistical optimality. The rationale is multiple genuinely distinct
contexts, window-level estimation, leave-one-window-out stability, and tolerance
for up to two incomplete candidate epochs.

## 5. Provider snapshot and workload-context identity

`backend_snapshot_digest` is SHA-256 over canonical JSON of the complete
sanitized observable provider calibration snapshot: backend/configuration,
target operations and couplings, all observable per-qubit and per-gate
properties, calibration timestamp, and provider-visible relevant versions.
Credentials, CRN/instance identifier, job/session identifiers, queue state, and
local timestamps are excluded.

`workload_context_digest` is SHA-256 over canonical JSON of the subset that can
affect the frozen workload: backend; physical qubits; used couplings and gates;
their target/calibration properties; layout; transpilation configuration; 128
shots; runtime configuration; relevant Python/Qiskit/Runtime versions; workload
ID; dataset digest; and circuit semantic hash.

Mean T1, mean T2, readout-error summaries, gate-error summaries, and related
aggregates remain analysis features only. They are not sufficient context
identities. A backend-wide digest change with unchanged workload digest is
logged as background context variation and does not open a scientific window.

## 6. Fixed physical support

Before confirmatory outcomes, provider context alone selects the
lexicographically smallest provider-declared operational direct two-qubit edge
that supports the frozen workload, without ranking service outcomes. The
resulting preregistered primary support is physical qubits `[0,1]`,
initial layout `[0,1]`, and route `[[0,1]]`. Transpilation must keep every
two-qubit operation on that fixed pair and the captured target must support the
route. The rule was fixed without confirmatory outcomes; no pair/layout may be
changed because its results look better.

If the pair, layout, or route becomes non-executable, new submits stop, the
context is invalid, the partial window is handled under Section 16, and P5 uses
the preregistered recovery decision table. An alternative physical layout
requires a prospective amendment and a new support identity; it cannot be
silently substituted into this campaign.

## 7. Calibration-window definition

A candidate window requires all of the following:

1. backend `ibm_basquecountry`;
2. `confirmatory_instance`;
3. an available provider calibration timestamp;
4. an identical stable read-only snapshot confirmed twice at least 600 seconds
   apart;
5. for `w>1`, a timestamp strictly later than the prior accepted window; and
6. for `w>1`, a `workload_context_digest` different from the prior accepted
   context.

The `window_id` is SHA-256 over the instance alias, backend, provider calibration
timestamp, and workload digest. Elapsed time alone never opens a window. Before
every submit the runner revalidates instance alias, backend, operational state,
workload digest, and phase budget.

If the workload digest changes during acquisition, the runner stops all new
submits and marks the window incomplete without inspecting outcomes. Completed
partial data remain in the audit, resource, and reliability records but are
excluded from calibration, primary inference, and accepted-window analyses.
Data from two snapshots are never pooled into one window.

## 8. Acquisition and natural longitudinal transition

Window 1 performs 39 bootstrap calibration jobs, two supported verification
probes, then two controlled-OOS sensitivity probes. For every accepted `w>1`:

1. detect the later provider epoch and freeze both digests;
2. execute six pre-recovery service probes in the frozen randomized order;
3. replay P2, P4, and P5 decisions on the same sealed evidence where valid;
4. P2 evaluates with the accepted calibration from `w-1`, intentionally without
   a context guard;
5. P4 detects absent exact-stratum support and HOLDs before calibrated assurance;
6. P5 HOLDs and starts the complete 39-unit recalibration for epoch `w`;
7. after the new reference is ready, P5 re-evaluates held results that remain
   physically and semantically valid, without another QPU execution;
8. execute two post-recovery supported verification probes; and
9. execute two fixed optimization-level-2 sensitivity probes.

Thus each accepted later window has 39 calibration jobs, six pre-recovery
service jobs, two post-recovery jobs, and two controlled-stress jobs. Policy
replay does not multiply physical jobs. Six probes remain nested in one epoch.

## 9. Exact calibration rule

The primary `ContextSupportModel` is exact strata, named the **deterministic
context-support guard**. It is not evaluated as a scientific OOS classifier
against labels defined by the same exact-stratum membership. The empirical
question is whether prohibiting assurance outside declared support changes
validity and service consequences.

For each accepted epoch, `n_cal=39`. Greater nonconformity scores are worse. For
test score `s`, use the upper-tail rank with conservative ties:

`p(s) = (1 + count_i[s_i >= s]) / (39 + 1)`.

Every calibration score equal to `s` is included in the greater-than-or-equal
tail. The grid resolution is `1/40=0.025`; `alpha=0.05` is exactly `2/40`.
Reject calibrated acceptance when `p<=0.05`; accept only when `p>0.05`. The
equivalent finite threshold is the 38th ascending calibration order statistic,
subject to the p-value/tie rule above. Exhaustive small-case and tie tests are a
freeze gate.

A calibration expires immediately when the workload digest changes, the
provider timestamp/snapshot changes during acquisition, a required context
field becomes unavailable, fixed physical support is non-executable, or the
window is incomplete. A new epoch begins unsupported. Only its complete
39-unit block may create its reference; scores from different epochs are never
pooled. If calibration or required independent verification fails, support is
not asserted and P5 proceeds to fallback, rollback when eligible, or BLOCK.

## 10. Policy contrast

- P2 (`P2-global-calibrated`) is context-agnostic. At `w>1` it may continue to
  serve under the stale accepted reference from `w-1`; it does not silently
  claim that the new context is supported.
- P4 (`P4-context-oos-abstention`) is the mechanistic abstention baseline. It
  evaluates support before calibration and HOLDs an unseen exact stratum. P4 is
  not the primary scientific contrast because this HOLD is deterministic by
  construction.
- P5 (`P5-recovery-enforcement`) applies P4, enforces HOLD, performs the fixed
  recovery, re-evaluates, and returns safe service, FALLBACK, or terminal BLOCK.

The primary comparison is paired P5 versus P2. No result withheld by HOLD or
BLOCK is counted as served. No unannounced fallback is permitted.

## 11. Machine-readable service and assurance endpoints

For a policy/probe record:

`unsafe_service_continuation = served AND NOT oracle_service_correct`.

This is the primary H1 endpoint. Correctness comes only from the independent
frozen oracle in Section 12; policy action, exact-stratum membership, and
context-support labels do not decide correctness.

`assurance_invalid_continuation = served AND NOT
assurance_valid_for_serving`.

This is a secondary epistemic/assurance-validity endpoint. It does not imply
physical service failure. In particular, a correct result served under invalid
assurance is assurance-invalid continuation but is not unsafe service
continuation. The secondary contrast is `RD_assurance,w =
assurance_invalid_continuation(P5) -
assurance_invalid_continuation(P2)`. A strong assurance result cannot rescue,
replace, or be promoted over an unsupported H1.

Every served result is assigned exactly one machine-readable state:

1. `SERVICE_CORRECT_ASSURANCE_VALID`: oracle PASS and assurance valid;
2. `SERVICE_INCORRECT_ASSURANCE_VALID`: oracle FAIL and assurance valid;
3. `SERVICE_CORRECT_ASSURANCE_INVALID`: oracle PASS and assurance invalid; or
4. `SERVICE_INCORRECT_ASSURANCE_INVALID`: oracle FAIL and assurance invalid.

States 2 and 4 are unsafe service continuations. States 3 and 4 are
assurance-invalid continuations. A withheld result is `NOT_SERVED`, lies outside
the served 2x2 table, and is false for both continuation indicators.

The primary denominator is every paired P5/P2 pre-recovery probe in each usable
`w>1`; both policies must have one record for the sealed `probe_id`. The same
paired records support the secondary assurance contrast. The two endpoints and
all four served states are always reported separately.

The following service consequences must appear beside any claim of successful
assurance or recovery; they are not co-primary hypotheses:

- safe service completion/availability: eligible requests correctly served
  with valid assurance within 1,800 seconds of T0;
- recovery success as defined in Section 13;
- false hold: a supported, oracle-correct request terminally withheld beyond
  the 1,800-second service deadline (a resolved initial HOLD is reported as an
  initial hold, not a false terminal hold);
- decision, recalibration, and total time to recovery;
- fallback correctness: executed fallback passes the same frozen oracle and
  trusted invariants.

Report counts and denominators. Recalibration, rerun, fallback, and rollback
success are also separated. Resource endpoints include jobs, shots, QPU seconds,
wall time, observable queue time, recalibration count, reruns, and evidence size.

## 12. Frozen workload oracle

The independent reference is `exact-statevector-kernel-oracle-v1`. It constructs
the exact float64 statevector fidelity matrix for the frozen three-sample
ZZ-feature-map workload. A candidate is service-correct exactly when:

`relative_frobenius_error <= 0.15 + 1e-12` **and**
`maximum_absolute_error <= 0.20 + 1e-12`.

The comparison tolerance is `1e-12`; numerical precision is IEEE-754 float64;
NumPy is 2.4.6 and Qiskit is 2.5.2. Dataset digest:
`003bfc8878dcf731c26d268122f260692f56fc26a6655acb82e666422665a181`.
Circuit semantic hash:
`9d2a34dbe33a9bce977e5dd2e771b988dd75230e9cc74903896bda104c10795b`.
Implementation SHA-256:
`76e03c1ed8e13ed1d03e3e2495bc51a210448731ee411859a7203e30c9a0be3c`.
Oracle-contract digest:
`ef2c846e110565773521f0c7251350ef296ddf1bbf9f790ece6dc688c8c84231`.

The two thresholds are pilot-informed feasibility thresholds already declared
in `configs/pilot.v1.json`; they are frozen before confirmation and cannot be
derived from or changed in response to confirmatory outcomes.

## 13. Recovery semantics

`context_validity_restored` is true exactly when a request initially held
because context support was invalid follows the preregistered path, becomes
eligible after recovery with valid assurance, and violates no trusted invariant.
`service_correctness_restored` is true exactly when that request follows the
path, is served, passes the independent oracle, and violates no trusted
invariant. `recovery_success` requires both restoration indicators. Thus merely
making the context supported is insufficient. Context validity, service
correctness, and their conjunction are all reported.

P5 uses this order: binding/trusted-invariant failure -> BLOCK; unsupported or
expired context -> HOLD and 39-unit RECALIBRATE; valid held result and
assurance-reference-only change -> zero-QPU REEVALUATE; invalid result,
execution failure, or semantic/context requirement for physical execution -> at
most one RERUN per candidate window; unsafe candidate -> frozen classical
FALLBACK if available; eligible prior release -> ROLLBACK; otherwise BLOCK.

Re-evaluation reuses the held physical result and consumes zero QPU jobs. A
rerun creates one new physical execution and is permitted only for the three
conditions above. These paths, their costs, and their success rates are never
combined.

Record four monotonic timestamps:

- T0: context support becomes invalid or the request is held;
- T1: the recovery procedure starts;
- T2: calibration/recovery is ready; and
- T3: the request is safely served or terminally rejected.

Report decision latency `T1-T0`, recalibration latency `T2-T1`, and total
recovery latency `T3-T0`. Total is observed local wall-clock elapsed time. A
provider queue component is disaggregated only when observable; if unavailable,
it is missing and is neither imputed nor reported as queue latency. Passing the
1,800-second service deadline affects availability but does not erase a later
terminal recovery outcome.

## 14. Controlled OOS and exploratory models

Optimization level 2 versus supported level 1 is a predeclared secondary
sensitivity stress. Dataset, semantic circuit/workload, shots, backend, fixed
physical support, and runtime data are identical; only the declared
transpilation condition and its consequent compiled identity may change. Two
stress probes per accepted window are in the fixed order and budget. This stress
does not substitute for natural provider calibration drift and cannot be
changed or outcome-selected if H1 is weak.

Standardized distance and diagonal Gaussian support remain secondary/exploratory
only. They are not selected after confirmatory results. If the accepted epochs
do not support meaningful evaluation, they are omitted and left as future work.
The optimization-level-2 stratum is not promoted to supported service in this
campaign: P4 HOLDs, while P5 records that recalibration is not authorized for
this sensitivity stratum and uses the frozen classical FALLBACK or BLOCK.

## 15. Randomization and counterbalancing

`configs/randomization.v1.json` is the complete 484-job base list. It was
generated once before confirmatory outcomes with Python `random.Random` seed
`2509112026`. Calibration uses the fixed transpiler seeds 19062026 and 19062027
in a 20/19 split, alternating which seed receives 20 by window. Six-probe blocks
use 3/3 balance; two-probe blocks use 1/1. Three cyclic P2/P4/P5 replay orders
are balanced across probe identifiers. Blocks obey the causal acquisition order
in Section 8 and are never shuffled across it.

The SHA-256 digest of canonical JSON containing the assignment list is
`60c85a966b68a28bc09b9f826bc0f57612a449cd5dd86511e35619bcea2e441d`.
Regenerating or replacing the order after any confirmatory outcome is
prohibited.

## 16. Exclusions, incomplete windows, and stopping

Before outcome inspection, exclude from scientific analysis only duplicate
registry IDs; schema/digest-invalid evidence; confirmed provider cancellation
unrelated to the assigned workload; predeclared maintenance outage; or an
experimenter error before QPU execution. Every exclusion remains in the audit
and resource/reliability summaries. Execution failures, timeouts, context
missingness, unsafe results, HOLD/BLOCK, fallback failure, recovery failure, and
calibration failure are outcomes, not convenient exclusions. There is no
post-hoc outlier removal.

An incomplete window is excluded outcome-blindly under Section 7. Campaign
acquisition targets 10 accepted windows and permits at most 12 candidate epochs
to tolerate two incomplete epochs. Stop after 10 accepted windows, after 12
candidate epochs, or before the submit that would exceed either hard budget.
With 8–9 usable accepted windows, execute the registered primary analysis and
limit the claim accordingly. With fewer than 8, KC2 forbids a longitudinal
claim. Backend retirement, API semantics change, fixed-support failure that
cannot recover, or evidence-schema incompatibility stops acquisition pending a
prospective amendment.

## 17. Primary analysis

Within every usable `w>1`, pair P5 and P2 records by `probe_id`, calculate each
policy's oracle-based unsafe-service-continuation rate over the six probes, and
retain `RD_service,w`. Show all window-level P5 rates, P2 rates, and RDs. Across
the `W` usable transition windows, estimate the arithmetic mean `RD_service` and
its two-sided 95% small-sample t interval over the `W` RDs. The window is the
unit passed to the interval.

Compute `RD_assurance,w` from the same paired records and summarize it as a
secondary endpoint, explicitly separated from service failure. It cannot rescue
H1. Recovery success, context-validity restoration, service-correctness
restoration, availability, false hold, time to recovery, and fallback
correctness are secondary/mandatory companion outputs.

Show leave-one-window-out mean RDs. A window-cluster bootstrap and exact
paired/sign test are sensitivities only. Neither jobs, circuits, nor shots
increase `W`. Policy-specific endpoint rates retain numerator, denominator, and
Wilson 95% intervals where defined; zero denominators produce a null estimate.
All windows and failed/negative cells are shown.

No formal power claim is made from 10 windows. H3 is descriptive/secondary at
the transition level. Deterministic exact-stratum membership is not relabeled as
OOS sensitivity/specificity.

## 18. Budget

The pilot consumed 10 QPU seconds for four pilot jobs, or 2.5 seconds/job. The
prospective guard uses a conservative 3.0 seconds/job planning estimate.

- Accepted-window base: 390 calibration + 54 pre-recovery + 20 verification +
  20 controlled-stress = 484 jobs and 1,452 QPU seconds.
- Incomplete-epoch contingency: at most 2 x 49 = 98 partial jobs.
- Physical-rerun contingency: at most 12 jobs; held-result re-evaluation and
  classical fallback consume zero QPU jobs.
- Hard caps: 594 jobs and 1,782 QPU seconds.

Against 30,083 seconds available at design time, base and hard-cap fractions are
approximately 4.83% and 5.92%. Availability of the remaining quota does not
authorize spending it. The old 250-job/750-second proposal is superseded.
Every provider submit must pass the confirmatory `PhaseBudgetGuard` with its
conservative estimate; overrun blocks before provider submission.

## 19. Kill criteria KC1–KC6

- KC1 — no qualifying physical evidence: no physical-execution assurance claim
  if access, quota, fixed support, or provider execution fails.
- KC2 — insufficient longitudinal evidence: fewer than 8 usable accepted
  workload-relevant windows means no longitudinal claim.
- KC3 — stale-calibration degradation absent: if genuine transitions show no
  declared validity or correctness degradation, report that result and limit
  the mechanism claim; do not replace transitions post hoc.
- KC4 — P5 failure: if H1 is unsupported or recovery fails to preserve useful
  service, publish the negative result and make no successful assurance/recovery
  claim.
- KC5 — required service consequence unavailable: if completion/availability,
  recovery success, false hold, time to recovery, or fallback correctness cannot
  be measured, no successful recovery claim is allowed.
- KC6 — controlled OOS/transfer infeasible: omit the controlled sensitivity and
  make no configuration-transfer, FMS, QAOA, WP5, or global demonstrator claim;
  H1 remains unchanged.

Kill criteria are reported, never hidden or used to outcome-select a replacement
analysis.

## 20. Freeze record and gate

At freeze, all eight machine-readable configs passed their Draft 2020-12
schema; exhaustive calibration/tie tests, digest/window tests,
policy/recovery/endpoint/timestamp tests, instance and budget guards, and
randomization digest tests passed; the secret scan passed; and a complete
SimulatorAdapter/synthetic-epoch dry run produced evidence envelopes, both RD
builders, four-state classifications, analysis, and final tables. The dry run
is infrastructure validation only and never scientific evidence.

Freeze identity:

- timestamp: `2026-09-14T09:03:33Z`;
- commit: the immutable commit dereferenced by annotated tag
  `paper25-prereg-v1` (the tag and final freeze report carry its literal SHA;
  embedding a commit's own SHA inside that commit is self-referential);
- `configs/confirmatory_design.v1.json`:
  `558cb23b3bbb7f3da08321fcc1bf9c9c81271cd6075cfae6a183e419879bf2fc`;
- `configs/context_window_definition.v2.json`:
  `66b887d16d3e0cbdee437fe46771ba3a885550562625ebd3a6f0e43df3d48f89`;
- `configs/context_support_strategy.v2.json`:
  `2449b39e6bd0a2ff46a9679255d009174aa059b436d5db64daf64b0ca7c1b5a0`;
- `configs/qpu_phase_budgets.v2.json`:
  `ecc959918c3f894d10cbde12f07d4d5fdfd33e922601621426a7923345912375`;
- `configs/hypotheses.v1.json`:
  `5582dcaeba6ae235f5b33284039913e15b618623d3005df0746a15752674b860`;
- `configs/analysis_plan.v1.json`:
  `bee85ff5bfac24a64aa40cf73b6f5d4642b630a0b10d58529da97a7840941292`;
- `configs/randomization.v1.json`:
  `d423f404f0519402276475a055b3deb12a32a2abae3a0a33cd2304d2461defc5`;
- `configs/recovery_policy.v1.json`:
  `b68d620eeacd7f23c45e1e564c81f057496fe3ad0899f91155c664a93f2d75aa`;
- workload/oracle implementation:
  `76e03c1ed8e13ed1d03e3e2495bc51a210448731ee411859a7203e30c9a0be3c`;
- oracle contract:
  `ef2c846e110565773521f0c7251350ef296ddf1bbf9f790ece6dc688c8c84231`;
- primary analysis implementation:
  `5eb8a34bb836e60e9deddc509beae72ece72ee5f15c8e9e76550775629748a33`;
- endpoint-table builder:
  `2ed58346b391727937ac0a16a6ff92cc1886d4981d9b4439124cc3248da32c54`;
- dry-run builder:
  `651e3931566a76df31c599d2c2464075b72ec0d5720628866692788075122b03`;
- randomization assignment digest:
  `60c85a966b68a28bc09b9f826bc0f57612a449cd5dd86511e35619bcea2e441d`.

No frozen design file may change during the campaign. Any subsequent bug or
required design change uses a prospective versioned amendment. Confirmatory QPU
jobs at freeze: **0**. The first window was not executed.
