# AMENDMENT 003 — Campaign B write-once execution-contract launch records

Status: technical amendment authorized by the author on 2026-10-12 after the read-only
provenance diagnostic of the same day. Intended tag `paper25b-prereg-v1-amend3`. The original
tag `paper25b-prereg-v1` (freeze commit `fccb712c…`, tag object `cf7616be…`), the AMENDMENT 001
tag `paper25b-prereg-v1-amend1` (commit `3a23b2fe…`, tag object `dade5310…`) and the AMENDMENT 002
tag `paper25b-prereg-v1-amend2` (commit `88f65e92…`, tag object `325d76b5…`) are immutable and do
not move. Manifest: `configs/campaign_b/amendments/AMENDMENT_003.v1.json` (earlier manifests are
never overwritten). Candidate document:
`docs/campaign_b/AMENDMENT_CANDIDATE_2026-10-12_execution_contract_manifest_scope.md`.

**SCIENTIFIC_CHANGE = NONE. PHYSICAL_EVIDENCE_CHANGED = 0. NEW_QPU_SUBMITS = 0.
C04_CONSUMED = FALSE. CANDIDATE_EPOCHS = 3/16. USABLE_TRANSITIONS = 1/10.
SCIENTIFIC_LEDGER UNCHANGED (116 entries / 348 s conservative estimate / 88 provider jobs).**
The first C04 launch of 2026-10-12T10:33:28Z reached `candidate_gated` only and was halted by
operator STOP at 10:43:39Z before `window_open`; no candidate epoch was consumed and nothing is
restarted by this amendment.

## A. Root cause (accepted by the author)

`_record_contract` in `experiments/run_campaign_b.py` (AMENDMENT 001) rewrote
`artifacts/confirmatory/campaign_b/campaign/execution_contract.json` in place at every launch
with a new `verified_at`. The frozen campaign-manifest builder
(`src/athena_aegis/campaign_b/manifests.py`, freeze baseline, untouched by any amendment) pins
every file of the campaign namespace outside `MUTABLE_FILES = (STOP, campaign_state.json,
events.jsonl, polls.jsonl)`. The per-launch file is not in that list, so every launch invalidated
exactly the `execution_contract.json` entry of every campaign manifest written before it. No frozen
text declared the file mutable; the two frozen layers were individually correct and jointly
inconsistent for this one file. Reproduction is offline and deterministic (compare the manifest
entries with the working tree after any later launch; `git diff <sealing commit>..HEAD` on the file
shows `verified_at` only, C01 additionally the AMENDMENT 002 keys).

## B. Exact patch (one frozen file, one function)

`experiments/run_campaign_b.py`: old SHA-256 `2b69e104ee121c7c01673bebe6f95e17e1bbe37dacbb8b22fd26aa025d07b8da`,
new SHA-256 `ce7051b8bc890cbc93c94498829b6c479475e688aa3a61db2c644d3b10b1711e` (recorded in the
manifest). Every other frozen file is byte-identical to the AMENDMENT 002 stage (43 of 44; 38
unchanged since the freeze).

1. `AMENDMENTS` gains the third overlay; `EFFECTIVE_CONTRACT` names the four tags.
2. `_record_contract(campaign_dir, root, report, effective, subset)` writes one **write-once launch
   record** `execution_contracts/<launch_id>.json` per launch, where
   `launch_id = <UTC YYYYMMDDTHHMMSSffffffZ>-<first 12 hex of the record digest>` (deterministic
   from content and UTC time; no `:` or other Windows-reserved characters). The record carries the
   effective contract actually verified, `verified_at` (UTC, `Z`), original tag / freeze commit /
   tag object, every amendment (id, tag, manifest digest, commit when git is available), the 44
   effective frozen digests, the 29-key runner identity scope,
   `provider_interaction_before_verification = false`, the legacy snapshot's presence and digest,
   `launch_id` and `record_digest_sha256`. No secret and no private identifier is ever included.
3. `_write_once` stages `<name>.json.tmp` in the same directory, fsyncs, publishes atomically by
   hard link (exclusive create where hard links are unavailable) and re-hashes the published bytes.
   An existing target or staging path raises `ContractViolation` **before any provider object is
   constructed**; nothing is ever overwritten or truncated.
4. The append-only `execution_contract_verified` event is kept, first in `events.jsonl`, and now
   names `launch_id`, `launch_record`, `launch_record_sha256` and
   `legacy_execution_contract_rewritten = false`.
5. `execution_contract.json` is never written again. Helpers `launch_id_for`, `launch_records`
   and `_write_once` are added; `verify_effective_contract`, `effective_frozen_digests`,
   `runner_identity_subset`, the provider construction order and the runner call are unchanged.

## C. Legacy snapshot

`artifacts/confirmatory/campaign_b/campaign/execution_contract.json` is a **legacy historical
snapshot**: 1973 bytes, SHA-256 `ad9fe1fbadac7739df4dafd80384daadce6063ecad1b20730288dd421dc38403`,
last written by the launch of 2026-10-12T10:33:28.953494Z, committed in `24a313e…`, pinned in the
manifest and verified by `scripts/campaign_b/verify_amendment_003.py` and test F. It must not be
used as evidence that the current contract was just verified; for every launch the current
verification is the launch record named by that launch's `execution_contract_verified` event.
Consumer audit: no code reads the file except the entrypoint writer (removed) and
`tests/campaign_b/test_amendment_001.py` (updated to the launch record); the runner, analysis,
verifiers and schemas never read it.

## D. Historical manifests C01–C03 (preserved exactly, never regenerated)

| Manifest | Sealing commit | Entries | At sealing commit | Working tree now |
|---|---|---|---|---|
| `manifests/C01.json` | `365c73d1…` | 6 | 6/6 | 4 full, 1 append-only prefix (ledger), 1 documented exception |
| `manifests/C02.json` | `adf83f2…` | 15 | 15/15 | 12 full, 2 append-only prefix (ledger, registry), 1 documented exception |
| `manifests/C03.json` | `785b071…` | 23 | 23/23 | 22 full, 1 documented exception |

The documented exception is exactly the `execution_contract.json` entry of these three manifests
(`campaign_support`, `scientific_evidence = false`, `supports_scientific_evidence = false`) with
its original hashes recorded in the manifest (`402e48e8…` / 743 B for C01, `ba2d238f…` / 1973 B for
C02, `f921b56d…` / 1973 B for C03) and the documented difference to the legacy snapshot
(`verified_at` only; C01 additionally the AMENDMENT 002 keys). It is not a generic allowance: the
verifier and test F accept it only for these manifests and these hashes, and any other mismatch
fails. Normative rule recorded by this amendment: campaign manifests are close-time snapshots;
entries for append-only provenance files (`ledger.jsonl`, `registry.jsonl`, `late_results.jsonl`)
verify by manifest-sized byte prefix after later windows; every other entry must match in full
indefinitely. Campaign manifests written after this amendment (C04 onwards) pin the write-once
launch records and verify in full after any number of later launches (test G, verifier section
`post_amendment_campaign_manifests`, no exception admitted). `manifests.py` and its exclusion list
are unchanged; no reproducible technical need to change them exists.

## E. Scientific non-change

Unchanged: H1-B, primary endpoint, safety gate, fallback rule, retained-result rule, availability
gate, queue threshold, polling, binding J1–J4, context definition, reference selection,
randomization, bootstrap ordering, assignments, acquisition commitment, shots, physical support,
window target, candidate cap, 24 h cap, 90-day cap, budget, KC-B1…B9, analysis, oracle, provider
submission path, state machine. Evidence impact: documentary provenance only; every sealed
scientific record, every window manifest and every historical campaign manifest is byte-identical.

## F. Tests, verifier and effective contract

`tests/campaign_b/test_amendment_003.py` (mandatory, A–L): two launches create two distinct
records; the second launch leaves the first record and a legacy snapshot byte-identical; names are
Windows-safe; a collision fails closed before provider construction; the event is kept and names
its record; C01–C03 verify at their sealing commits with the limited exception; a manifest written
after the amendment stays valid after later launches; the current contract is read from the launch
record, not the legacy file; only the entrypoint changed and the fake launch reaches the gate with
zero submits; Campaign A byte-identical; prior tags unchanged; no QPU job.
`tests/campaign_b/test_amendment_002.py` stays mandatory. `scripts/campaign_b/verify_amendment_003.py`
verifies the four-stage chain, the tagged trees, the legacy pin, the limited historical exception,
the launch records and the post-amendment manifests.

Effective contract after this amendment:
`paper25b-prereg-v1 + paper25b-prereg-v1-amend1 + paper25b-prereg-v1-amend2 + paper25b-prereg-v1-amend3`.

Campaign B stays halted behind STOP after this amendment: 0 runners, no persistent polling, no
C04, no C05, no QPU submit, no push; the earlier C04/C05 authorization awaits the author's renewed
confirmation after reviewing this amendment.
