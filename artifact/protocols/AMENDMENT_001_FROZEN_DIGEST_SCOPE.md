# AMENDMENT 001 — Campaign B frozen-digest verification scope

Status: technical amendment authorized by the author on 2026-10-07, pre-acquisition.
Intended tag `paper25b-prereg-v1-amend1`. The original tag `paper25b-prereg-v1`
(freeze commit `fccb712c34f40a647f7d3b2d6171b4f2d48ba082`, tag object
`cf7616bec56bdd89d6360d1f19294fd7338366fa`) is immutable and does not move.

**SCIENTIFIC_CHANGE = NONE. QPU submits before amendment = 0. Evidence created before
amendment = none. Acquisition = NOT STARTED.**

## Root cause

The frozen live entrypoint `experiments/run_campaign_b.py` passed the complete
44-entry `frozen_sha256` map of `configs/campaign_b/freeze_record.v1.json` as
`expected_frozen_digests` to the frozen `CampaignBRunner`. The frozen
`verify_frozen_identity` recomputes digests only for its intended scope (11
configs plus the 18 `FROZEN_SOURCE_FILES`, 29 keys) and raises `CampaignHalt` for
any expected key it did not compute. The 15 keys outside that scope (six schemas,
the entrypoint itself, two scripts, six package modules) therefore produced a
deterministic halt, `frozen file digest mismatch: experiments/run_campaign_b.py`,
before any provider polling, submission or evidence creation, although all 44
files were byte-identical to the frozen tag. Reproduced offline with a null
provider (`docs/campaign_b/AMENDMENT_CANDIDATE_2026-10-07_frozen_digest_scope.md`).

## Exact patch (Option 1, minimal)

Only `experiments/run_campaign_b.py` changes (old SHA-256 `e571a69c…`, new
`6a615629…`, both recorded in `configs/campaign_b/amendments/AMENDMENT_001.v1.json`):

1. `verify_effective_contract(root)` verifies, fail-closed and before any provider
   object exists, every one of the 44 frozen files against the effective
   contract: the original freeze baseline overlaid with the amendment manifest's
   `new_sha256` for the affected file. The key set must equal the 44-file baseline
   exactly (no extra or missing key); the manifest may only overlay files inside
   the baseline and its `old_sha256` must equal the baseline. With git available
   it also requires `paper25b-prereg-v1 → fccb712c…` and the presence of
   `paper25b-prereg-v1-amend1`.
2. `runner_identity_subset` hands the frozen runner only the 29-key subset
   (`configs/campaign_b/*` in `CONFIG_FILES` plus `FROZEN_SOURCE_FILES`) that
   `verify_frozen_identity` is contractually responsible for recomputing. The
   runner's own check is unchanged and still halts on any mismatch of those keys.
3. The verified contract is written, before the runner starts, as an
   `execution_contract_verified` event in `events.jsonl` and as
   `execution_contract.json` in the campaign namespace, naming the effective
   contract `paper25b-prereg-v1 + paper25b-prereg-v1-amend1`.
4. `launch()` is the single path from verification to provider construction;
   `main()` still refuses without `--live`.

`verify_frozen_identity`, the runner and every other frozen file are byte-identical
to the freeze (43 untouched files verified by `scripts/campaign_b/verify_amendment_001.py`).

## Scientific non-change

Unchanged: H1-B, primary endpoint, safety gate, fallback rule, 10-window target,
16-epoch cap, availability gate, polling cadence, context binding, state machine,
P2 reference semantics, randomization, bootstrap ordering, assignment digest,
acquisition commitment, budget, rerun semantics, KC-B1…B9, analysis, oracle,
shots/layout/support. Both verification layers are stricter than before, never
weaker.

## Effective pre-flight contract

Future live execution verifies `paper25b-prereg-v1` plus `paper25b-prereg-v1-amend1`
as the effective immutable execution contract and records it in its
event/provenance record before any provider interaction. Any further
scientifically relevant correction requires `paper25b-prereg-v1-amendN`.
