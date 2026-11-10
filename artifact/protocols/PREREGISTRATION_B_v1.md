# Preregistration B v1 — FREEZE CANDIDATE — NOT YET FROZEN

Study: Campaign B. Context-conditioned recovery after genuine physical-QPU
workload-context transitions admitted by a frozen availability gate.

Status: freeze candidate prepared 2026-10-06 from the author's decisions of the
same date. The annotated tag `paper25b-prereg-v1` does **not** exist. No Campaign B
provider job has been submitted. This document becomes normative only when the
author approves it and creates the tag; until then every value below is a
candidate. Campaign A (`paper25-prereg-v1`, closed) remains byte-identical and is
never modified; its outcomes never enter Campaign B confirmatory evidence.

## 1. Scientific contract and population

Research question: after a genuine physical-QPU workload-context transition
admitted by the frozen Campaign B availability gate, can context-conditioned
recovery restore correct and assurance-valid service within a bounded deadline
without requiring physical re-execution of the held service probe?

Primary population: `pi_B = P(window_recovery_success | genuine workload-context
transition admitted by the frozen Campaign-B availability gate)`. This
conditioning is part of the claim. Campaign B does not claim recovery reliability
at arbitrary provider congestion states, and every statement about `pi_B` in the
manuscript must carry the gate conditioning.

Campaign A is development and hypothesis-generating evidence only. Its
operational metadata (queue depth, status message, timestamps, completed versus
locally timed-out attempts) was used to derive the availability gate (Section 6);
its scientific outcomes were never inspected for that derivation and never enter
Campaign B evidence.

## 2. H1-B and exact analysis

- H0: `pi_B <= 0.5`. H1-B: `pi_B > 0.5`.
- Test: exact one-sided binomial with `n = 10` usable transition windows,
  `alpha = 0.05`. Rejection region: `X >= 9` successes.
- Report: `X/10`, the exact one-sided p-value, the two-sided 95% Clopper–Pearson
  interval, the one-sided 95% lower bound, every individual window, and
  leave-one-window-out success counts.
- Wording constraint: `X >= 9` establishes evidence against `pi_B <= 0.5` under the
  gate-conditioned population. It must not be described as proving population
  reliability `>= 0.90`. The operational criterion (9 of 10) and the statistical
  null (0.5) are distinct.
- Failure rule: if `W < 10` usable windows exist at stop, H1-B is NOT TESTED / NOT
  ESTABLISHED. No reduced-`n` test, mid-p correction, Bayesian summary or
  alternative test may be substituted.
- Implementation: `src/athena_aegis/campaign_b/statistics.py` (exact binomial with
  `math.comb`; intervals by bisection; no SciPy dependency). Reference values:
  p(9/10) = 0.0107421875, p(8/10) = 0.0546875, CP95(9/10) = [0.555, 0.997], one-sided
  lower bound(9/10) = 0.606, (10/10) = 0.741.

## 3. Primary endpoint and fallback non-triviality

A primary probe succeeds (`recovered_valid_service`) if and only if:

1. a physical held service probe exists and is context-bound (Section 8);
2. final service is served;
3. `oracle_service_correct = true` (determinate);
4. `assurance_valid_for_serving = true` (determinate);
5. `total_recovery_latency_seconds <= 1800` on the local clock T0→T3;
6. `service_probe_qpu_rerun = false`;
7. trusted invariants held.

Any indeterminate value fails the probe (fail closed).

`window_recovery_success` holds if and only if all six primary probes succeed, at
least 5 of 6 are restored by retained-result re-evaluation, and at most 1 of 6 uses
the frozen classical fallback.

Classical fallback is admissible only after a valid context-bound physical held
result exists, the 39-unit context-bound recalibration and zero-QPU re-evaluation
have been performed, and the frozen calibrated rule determines that retained-result
serving is not admissible (`p <= 0.05`). Fallback may not rescue missing physical
service evidence, failed context binding, an unknown oracle state, or execution
failure before a held result exists. A window with an incomplete reference, an
unbound primary probe or a missing held result is non-usable, never a success.
Unlimited fallback therefore cannot make the primary endpoint trivially successful.

Usable transition window (decided outcome-blind): gate-admitted genuine transition;
all six primary probes with exactly one bound sealed attempt; 39 of 39 calibration
units bound forming the complete reference; zero-QPU re-evaluation completed before
context expiry; integrity verification passed. Verification probes are secondary
and their absence does not void a window.

## 4. Safety gate

Primary success is impossible, regardless of `X`, if any primary P5 service is
served and oracle-incorrect, served with an indeterminate oracle, served with
invalid or indeterminate assurance, or served with failed or indeterminate context
binding. Fail closed. The safety gate is reported regardless of H1-B. A
descriptive safety report over all accepted windows and verification probes is
also published; it cannot rescue anything.

## 5. Physical design (variant R)

- Backend `ibm_basquecountry` on `confirmatory_instance`; fixed physical qubits
  `[0,1]`, layout `[0,1]`, route `[[0,1]]`; 128 shots; workload
  `paper15-kernel-regression-v1`; oracle `exact-statevector-kernel-oracle-v1`
  (thresholds 0.15 / 0.20); nonconformity score = relative Frobenius error versus the
  exact statevector reference; calibration rule `p = (1 + count(cal >= s)) / 40`,
  reject at `p <= 0.05`. All reused unchanged from Campaign A; no outcome-informed
  tuning.
- Per transition window: 6 primary held-service probes, 39 calibration units, 2
  secondary verification units = 47 physical jobs. Bootstrap: 39 + 2 = 41. Base
  design 41 + 10 × 47 = 511 jobs. Campaign A's controlled OOS stress probes are
  removed.
- Execution order is A-faithful and sequential: six probes one at a time, each held
  on seal; 39 calibration units; zero-QPU re-evaluation; two verification probes.
  One job in flight; no concurrent probes; no early recalibration; no optimization
  based on observed outcomes.

## 6. Availability gate (derived from Campaign A operational metadata)

A candidate opens only when the backend is operational, the provider status
message is `active`, `pending_jobs <= 5`, the fixed physical support is executable,
the workload-context digest is genuinely new (and the provider calibration
timestamp strictly later) relative to the last accepted context, and the context is
confirmed stable by two qualifying snapshots at least 600 s apart. The gate must
hold at candidate detection, at confirmation and immediately pre-open. Gate
failure before opening never consumes a candidate epoch. After a window opens no
scientific unit is throttled by queue depth; queue depth is recorded continuously
as operational metadata.

Derivation (`configs/campaign_b/gate_derivation.v1.json`, development-phase
infrastructure evidence, scientific outcomes never inspected): among Campaign A's
524 submitted attempts, 0 of 411 attempts at depth `<= 5` timed out once the single
attempt submitted under `status_msg = "maintenance"` is excluded by the status rule,
while 30 of 112 at depth `> 5` did; provider queue wait of completed attempts at
depth `<= 5` had maximum 4.0 s versus p90 21 s and maximum 1244 s at depth 6–10;
depth `<= 5` held during about 63% of campaign time. Maintenance status appeared
in 4 of 634 polls, both times at the opening of later-damaged epochs.

Polling cadence (frozen): discovery 1800 s; candidate present but gate closed
300 s; confirmation interval `>= 600` s. Read-only polls consume no scientific
unit.

## 7. Provider-aware job state machine

Campaign A's local 3600-s scientific timeout is removed. QUEUED is never an
execution failure. Provider terminal states are DONE, ERROR and CANCELLED.

Scientific termination. At workload-context expiry or 24 hours after
`window_open`, the scientific window terminates immediately and irrevocably: it can
never subsequently become usable, no new scientific submit may occur, and the
termination reason recorded at that instant never changes. Usability is decided
only on evidence bound before termination; a window whose primary set and
zero-QPU re-evaluation completed before termination (termination during the
secondary verification phase) keeps its usability. For jobs in flight at
termination: QUEUED/INITIALIZING jobs receive a provider cancellation request and
races are reconciled by the existing fail-closed rules; RUNNING jobs are never
cancelled and their provider state is read only for reconciliation and
provenance. Any result that becomes DONE after scientific termination is a
`post_window_terminal_result`: audit-only, `scientific_evidence = false`; it
cannot enter calibration, cannot enter the P2/P4/P5 endpoints, cannot create or
repair a reference, cannot restore window usability and cannot change the
terminal reason. Historical context binding is still performed on it for
provenance, but binding never promotes it into scientific evidence. A job that
stays non-terminal 900 s after a cancellation request is left open and reconciled
read-only at the next preflight under the same classification. DONE units observed
before termination become `BOUND_SEALED` or `UNBOUND_AUDIT_ONLY`; no scientific
outcome is inspected before this classification. Reruns: at most one physical
rerun per window, only after a terminal provider ERROR/CANCELLED or a submit
exception before a held result exists, never because a job waited in QUEUED, never
after HOLD, never after termination.

## 8. Context-at-execution binding (J1–J4)

Required evidence: provider `created`, `running`, `finished` timestamps; local
pre-submit and post-result snapshots; historical provider properties and target
queried at `running_at`; the frozen workload-context projection; integrity checks.
A unit is bound only when J1 (provider DONE with monotonic timestamps), J2 (both
local snapshots carry the window digest), J3 (historical projection at
`running_at` equals the window digest) and J4 (result integrity) all hold;
otherwise it is `UNBOUND_AUDIT_ONLY`. No `calibration_id` pinning is assumed because
the provider does not expose it post-submit. Preflight performs a read-only
historical-binding self-test against a sealed Campaign A job (provider `running`
timestamp 2026-09-20T20:40:08.581731Z, expected workload digest
`fe5806e61c93b9e54fa0c80002033c343c4e805ebaeb673e595b52c68a9befbd`); failure is
fatal (KC-B3) and no job is submitted.

## 9. P2 stale-reference semantics

P2 evaluates a new transition with the most recent prior accepted context whose
39-unit calibration reference is complete, context-bound and integrity-verified.
Primary-window usability is irrelevant to reference eligibility: an accepted window
with service-probe failures may supply the reference; an accepted window with an
incomplete or unbound calibration may not. With no valid prior reference, P2 is
`CALIBRATION_INVALID`. Each P2 record carries `reference_window_id`,
`reference_context_digest`, `number_of_context_transitions_since_reference` and
`reference_age_seconds`. There is no fallback to an incomplete reference.

## 10. Randomization

Seed: `int.from_bytes(SHA256("ATHENA-AEGIS|Campaign-B|paper25b-prereg-v1|2026-10-06|PID2024-155693NB-C43"), "big")`
= 32176565629066749733716970283081556674400995589604686629603279543945250232177.
PRNG: CPython 3.11 `random.Random(seed)` (MT19937) with `random.shuffle`,
block-wise. One preregistered 47-unit block per candidate epoch (B01–B16, 752
assignments); a bootstrap epoch executes only the 41 calibration and verification
units of its block; no two windows share a randomization; no Campaign A assignment
is reused. Transpiler seed set {19062026, 19062027} is part of the unchanged
projection and is only re-balanced. Assignment digest:
`6ce29dc6d8306916cd611d3e94d17cb6cd97da43b2edce994a23e0b3cda8fae8`
(`configs/campaign_b/randomization.v1.json`). Generated once; never regenerated
after the first Campaign B submit.

Bootstrap ordering. A bootstrap epoch executes exactly the 41 calibration and
verification units of its own block in the block's preregistered sequence order;
no additional random choice exists, so the ordering is deterministic and
preregistered by hash (`bootstrap_execution.orderings`, one 41-unit list per block
B01–B16, digest `fbc4b67a…`). Acquisition commitment: the record cryptographically
binds the seed phrase, the seed integer, the hash and byte-to-integer rule, the
PRNG and shuffle implementation with the Python version, the bootstrap rule and
orderings with their digest, and the B01–B16 assignments with their digest, into
`acquisition_commitment.commitment_digest` (`f193ac91…`; full values in the
config). The runner recomputes the commitment at every preflight and halts on any
mismatch, and refuses to open a bootstrap epoch whose execution order differs from
the preregistered ordering.

## 11. Stopping rules and window cap

Target: bootstrap + 10 usable transition windows. Maximum 16 candidate epochs.
The campaign stops at the first of: 10 usable transition windows; 16 candidate
epochs; the campaign hard cap; the provider quota guard; a fatal kill criterion;
90 calendar days after the first submit; 30 consecutive calendar days without a
gate-open opportunity. No outcome-based optional stopping. Candidate rollover or
a closed gate before window open consumes no epoch. Maximum window wall-clock
lifetime after `window_open` is 24 hours; context expiry remains an earlier
scientific boundary.

## 12. Budget

Base 511 jobs. Campaign hard cap 810 submitted jobs: bootstrap 41 + 16 candidate
blocks × 47 = 793, plus at most one authorized acquisition rerun per candidate epoch
= 809, so that candidate cap, rerun allowance and resource cap are mutually
coherent. Conservative QPU-time hard cap 2430 s (3 s per job); provider-observed
cost in Campaign A was 2 s per job. The global caps remain even if the provider
quota period resets. Provider allocation/period metadata is captured read-only at
freeze and at every preflight. Read-only check of 2026-10-07T09:23Z: allocation
120 000 s in a rolling 28-day window, consumed 2 798 s, remaining 117 202 s; the
hard cap is 2.03% of the allocation and 2.07% of the remaining quota (the
2026-10-06 read showed 138 000 s, so the live allocation is re-read at freeze). A
window opens only if 47 jobs and 141 QPU s fit under both caps and the provider
quota permits them.

## 13. Secondary endpoints

Retained-result-only recovery success; number and fraction of fallbacks; recovery
latency T0–T3 (decision, recalibration, total); observable provider queue wait;
recalibration cost; service availability; P2 and P5 assurance-invalid continuation
(mechanistic secondary, not H1-B); incorrect service continuation; verification-
probe behavior; missingness; binding failures; queue exposure; QPU/resource usage.
Rates carry numerator, denominator and Wilson 95% intervals.

## 14. Kill criteria

KC-B1 no physical evidence; KC-B2 fewer than 10 usable windows (H1-B not tested);
KC-B3 binding infeasible (preflight self-test failure fatal; any required UNBOUND
unit makes its window non-usable; campaign-level fatal when `>= 20%` of scientific
terminal units are UNBOUND once `>= 50` terminal units exist; unbound fraction
reported continuously); KC-B4 recovery correctness failure; KC-B5 safety-gate
violation; KC-B6 service consequence not measurable; KC-B7 provider/API semantics
incompatible (fatal); KC-B8 budget/quota; KC-B9 operational infeasibility (30 days
without a gate-open opportunity, or the 90-day cap). No replacement threshold is
invented during acquisition. See `configs/campaign_b/kill_criteria.v1.json`.

## 15. Campaign A immutability and independence

`configs/campaign_b/campaign_a_baseline.v1.json` pins the 105 git-tracked Campaign
A files (git tree `83fdbaa8336e3bd4aaeacc31e6f41a395206496a`). Every Campaign B
development verification, the freeze, every runner preflight, every evidence commit
and the final analysis call the fail-closed verifier
(`scripts/campaign_b/verify_campaign_a_immutable.py`). Campaign B code has no write
path into Campaign A evidence: every writer passes `guard_write_path`, and the
runner refuses a campaign directory inside the Campaign A namespace. Campaign B
evidence lives under `artifacts/confirmatory/campaign_b/`.

## 16. Development validation (no QPU)

The scripted fake provider exercised: normal fast queue; 8-hour queued then DONE in
the same context; queued across context expiry; running across context expiry;
cancel success; cancel/RUNNING race; late DONE; provider ERROR with one allowed
rerun; maintenance status; queue-depth gate; historical properties unavailable
(preflight-fatal and unit-level); historical properties inconsistent; accepted
window with an incomplete reference; accepted non-usable window with a complete
reference; fallback 0/6, 1/6 and 2/6; oracle indeterminate; assurance
indeterminate; W = 9 versus W = 10; the 9/10 versus 8/10 boundary; a Campaign A
mutation attempt; and the scientific-termination set: RUNNING at context expiry
then DONE, RUNNING at the 24 h cap then DONE, QUEUED cancel success, QUEUED
cancel/RUNNING race after closure, and no late completion reopening or repairing a
terminated window. A full dry run (bootstrap, ten usable windows, rollover, queue
stall, context expiry, one fallback, one accepted non-usable window with a complete
calibration reference, reference selection skipping an incomplete reference,
campaign close) ran on the fake provider only and is stored under
`artifacts/confirmatory/campaign_b/dry_run/` with `scientific_evidence = false`.
It is infrastructure validation, never scientific evidence.

## 17. Freeze gate

The freeze happens only after explicit author approval of the freeze-candidate
report. At freeze: the eleven configs under `configs/campaign_b/`, the schemas under
`schemas/campaign_b/`, the frozen source modules listed in
`athena_aegis.campaign_b.runner.FROZEN_SOURCE_FILES`, and this document are pinned
in `configs/campaign_b/freeze_record.v1.json` with their SHA-256 digests; the
annotated tag `paper25b-prereg-v1` is created; provider quota metadata is captured
read-only; Campaign A is re-verified byte-identical. Campaign B QPU jobs at freeze:
**0**.
