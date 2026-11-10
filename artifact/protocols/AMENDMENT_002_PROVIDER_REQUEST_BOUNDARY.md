# AMENDMENT 002 — Campaign B provider request boundary and pre-provider fatal classification

Status: technical amendment authorized by the author on 2026-10-10 after the B01
halt of 2026-10-09. Intended tag `paper25b-prereg-v1-amend2`. The original tag
`paper25b-prereg-v1` (freeze commit `fccb712c…`, tag object `cf7616be…`) and the
AMENDMENT 001 tag `paper25b-prereg-v1-amend1` (commit `3a23b2fe…`, tag object
`dade5310…`) are immutable and do not move. Manifest:
`configs/campaign_b/amendments/AMENDMENT_002.v1.json` (AMENDMENT 001's manifest is
never overwritten).

**SCIENTIFIC_CHANGE = NONE. Provider jobs before amendment = 0. QPU seconds before
amendment = 0. Acquisition physical evidence before amendment = none. B01 remains
candidate epoch 1/16, `incomplete_halt`, records byte-for-byte preserved.**

## A. Root cause (accepted by the author)

`CampaignBRunner._execute_unit` builds the submission's context metadata with the
eight shared request keys plus three Campaign-B-local provenance keys
(`candidate_id`, `label`, `phase`). `IBMCampaignBProvider.submit` forwarded the
complete mapping into the shared provider layer's `SubmissionRequest`, whose
validation admits only the shared keys and raised

```
ValueError: unsupported request context metadata: ['candidate_id', 'label', 'phase']
```

before `IBMRuntimeAdapter.submit` was invoked. No `SamplerV2` object and no
provider job ever existed: IBM jobs created 0, QPU seconds 0, physical evidence 0,
scientific outcome observed 0. The scripted fake provider consumed `Submission`
directly and never constructed the real `SubmissionRequest`, so the gap was
invisible offline, and the live submit path had never executed before B01.

## B. Provider-boundary patch (`src/athena_aegis/campaign_b/providers.py`)

- `CAMPAIGN_B_LOCAL_METADATA_KEYS = {candidate_id, label, phase}` declares the
  Campaign-B-local keys. They remain in Campaign B provenance (unit record fields
  `candidate_id`, `intended_label`, `assignment.phase` as before, plus the new
  `request_metadata.campaign_b_local` split) and never cross the boundary.
- The admitted key set is **not** re-declared: `contract_admits_metadata_key`
  asks the real shared `SubmissionRequest` contract (one offline probe per key,
  cached). `partition_request_metadata` keeps declared-local keys local, forwards
  keys the real contract admits, and fails closed on any other key
  (`PreProviderImplementationError`). The shared provider contract is unchanged.
- `build_provider_request` constructs the real `SubmissionRequest` from a
  Campaign B `Submission` with exactly the boundary keys.
- `IBMCampaignBProvider.submit` calls `build_provider_request` and only then
  `adapter.submit(request)`. A failure before the adapter raises
  `PreProviderImplementationError`; a failure inside `adapter.submit` keeps the
  frozen `SUBMIT_FAILED` semantics (conservative ledger charge, frozen rerun rule).

## C. Pre-provider fatal classification (`runner.py`, `constants.py`, schemas)

Second objective defect exposed by B01: the frozen runner classified a local
exception raised before adapter invocation as `SUBMIT_FAILED`, charged one
conservative ledger job, authorized the single per-window physical rerun and
advanced through the remaining scientific units (27 units, 28 attempts).

Correction (implementation safety, not scientific policy): every local step
between the frozen pre-submit gate and the provider adapter (transpile,
fixed-support check, metadata partition, `SubmissionRequest` construction) is
pre-provider. A failure there is recorded as the unit terminal state
`PRE_PROVIDER_IMPLEMENTATION_ERROR` with sanitized technical provenance
(`failure_category = pre_provider_implementation_error:<stage>:<ExceptionType>`,
provider message suppressed), `scientific_evidence=false`,
`physical_execution_evidence=false`, `provider_job_created=false`,
`job_id_pseudonym=null`, no ledger entry; the runner emits
`pre_provider_implementation_error` and raises `CampaignHalt`: no retry, no next
scientific unit, window closed `incomplete_halt`, campaign halted. Successful
submits now record `provider_job_created=true`.

Explicitly unchanged and covered by tests G, H, I and M: provider terminal
`ERROR` → `EXECUTION_FAILURE` and the frozen eligible-rerun rule; provider
terminal `CANCELLED` (provider-side rerun-eligible, runner-requested
`CANCELLED_BY_RUNNER`); adapter-level submit exception → `SUBMIT_FAILED`
(frozen conservative charge and frozen rerun rule, as listed in
`budget.v1.json#rerun_policy` "submit exception"); QUEUED/RUNNING semantics,
context expiry, 24 h cap, cancel grace, binding J1–J4, attempt selection,
KC-B1…B9.

## D. B01 historical treatment

Nothing in B01 is rewritten, deleted or regenerated. The window manifest's files,
`units.jsonl`, `manifests/C01.json` and `ledger.jsonl` are byte-identical to the
runner's evidence commit `365c73d1…` (test J). An append-only interpretation
layer, `artifacts/confirmatory/campaign_b/postwindow/B01_2026-10-09/amendment_002_classification.json`,
maps the 28 `SUBMIT_FAILED` records to the retrospective class
PRE_PROVIDER_IMPLEMENTATION_ERROR and the one `NOT_SUBMITTED` record to the
operator STOP. Author decisions recorded in the manifest: C01 remains consumed as
candidate epoch 1/16, no refund, no reset, no reuse of C01, no physical bootstrap
reference exists; the next candidate is C02 under the frozen state machine and
its bootstrap/transition role is determined mechanically by the frozen state
(`last_accepted_context` is null ⇒ bootstrap), never manually.

## E. Budget semantics audit — BUDGET SEMANTICS = A

Normative sources inspected before any accounting decision:

- `configs/campaign_b/budget.v1.json#job_accounting`: "every provider-accepted
  submission counts as one job (cancelled and late jobs included); conservative
  3 s per job at submit; provider-reported QPU seconds recorded separately".
- `configs/campaign_b/budget.v1.json#guard`: "PhaseBudgetGuard rebuilt from the
  Campaign B ledger before every submit"; `#rerun_policy.allowed_only_after`
  includes "submit exception".
- `manuscript/PREREGISTRATION_B_v1.md` §12: "Campaign hard cap 810 submitted jobs".
- `src/athena_aegis/campaign_b/budget.py` `guard_from_ledger`: "Every ledger entry
  is a submitted job (cancelled and late jobs included)".
- Frozen runner: a submit exception records a ledger entry with
  `provider_acceptance_confirmed=false` and charges 3 s (unit record
  `estimated_qpu_seconds=3.0` for `SUBMIT_FAILED`).

Determination: the frozen contract charges the conservative estimate at submit for
every attempt that reaches the provider boundary, confirmed or not;
provider-accepted submissions are the mandatory lower bound of what counts;
over-counting is the fail-safe direction. The 28 jobs / 84 s of B01 are therefore
preserved exactly, with no refund. A PRE_PROVIDER_IMPLEMENTATION_ERROR never
reaches the provider boundary, is not a submitted job under the frozen definition
and halts the campaign, so it creates no ledger entry; no existing accounting is
altered and the 810-job hard cap is untouched.

## F. Scientific non-change

Unchanged: H1-B, primary endpoint, safety gate, fallback rule, retained-result
rule, availability gate, queue threshold, polling, binding J1–J4, context
definition, reference selection, randomization, bootstrap ordering, assignments,
acquisition commitment, shots, physical support, window target, candidate cap,
24 h cap, 90-day cap, KC-B1…B9, analysis, oracle. SCIENTIFIC_CHANGE = NONE.

## G. Effective contract and verification

Effective contract after this amendment:
`paper25b-prereg-v1 + paper25b-prereg-v1-amend1 + paper25b-prereg-v1-amend2`.
`experiments/run_campaign_b.py` verifies the chain freeze → AMENDMENT 001 →
AMENDMENT 002 (every old digest equals the effective digest before it; key set
fixed at 44; parent-amendment commit and tag object checked) before any provider
object exists, and records it in `execution_contract_verified`.
`scripts/campaign_b/verify_amendment_002.py` verifies the same chain against the
working tree and the tagged trees; `tests/campaign_b/test_amendment_002.py` is
mandatory in Campaign B pre-release and preflight testing.

## H. Validation record

See the final AMENDMENT 002 report delivered to the author (sections I–R) and the
tag annotation of `paper25b-prereg-v1-amend2` for the executed validation list:
amendment tests, full Campaign B suite, full repository suite, effective-contract
verifier, AMENDMENT 001 verifier at its own tag, Campaign A immutability, secret
scan, `git diff --check`, scripted fake-provider scenarios, and exactly one live
read-only preflight through `launch()` with zero submits.

Campaign B stays halted behind STOP after this amendment: no persistent polling,
no C02, no QPU submit, pending author authorization.
