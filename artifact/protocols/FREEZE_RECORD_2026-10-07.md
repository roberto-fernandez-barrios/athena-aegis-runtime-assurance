# Campaign B preregistration freeze record (append-only)

- Tag: `paper25b-prereg-v1` (annotated, object `cf7616bec56bdd89d6360d1f19294fd7338366fa`) → freeze commit `fccb712c34f40a647f7d3b2d6171b4f2d48ba082`
- Freeze timestamp (UTC): 2026-10-07T10:29:48Z
- Frozen candidate files: 44; listing SHA-256 `a919ea7b6192c93a2515de9e7b83d6a52ebe5a29f6c845c72dd774337ea68742`; mismatches at recompute: []
- Campaign A tree `83fdbaa8336e3bd4aaeacc31e6f41a395206496a` (matches baseline: True); byte-identical at record: True
- Assignment digest `6ce29dc6d8306916cd611d3e94d17cb6cd97da43b2edce994a23e0b3cda8fae8`; bootstrap ordering digest `fbc4b67a3ea8dcc7c2b76d8079f9937ecfffba8972011972d25b24d0a9081fb9`; acquisition commitment `f193ac9114270e0a32d2d9a5b94605e9f888db021e28f43972500210e658b25c`
- Key file SHA-256:
  - preregistration: `1e02a38be3f3d1f489d17148b5c1afbf0a63517d69ccb83ff85c22c26e251e79`
  - hypotheses: `d5d252968f1c9b9bf2051556942488e57a940d2277765eddd85799bf0869291a`
  - analysis_plan: `a81a732b4be5089ec3c1ca61feed4e0e9548a1e3244328a7fb00d12fa6d9410b`
  - budget: `3f98aa327bf5192368e18ee87e60ef625fb4929971049beee036f2620ad6c3ed`
  - kill_criteria: `728ed21e035921d461504b3cf54a73ff71dc92cbaf224fa19d1d0bcd1671fe30`
  - runner_state_machine: `9b420a963e2723ebadc9e6684a59bde582a666e15bebd8c5267d7e6b784b39a2`
  - randomization: `e26699c6148bd9b55117052e978edd01cf2cfe673f1b7f71e3b9499021d56fda`
  - campaign_a_baseline: `e7051de1b36cc6524f84e9876ab42b8abbf7a9e36b6fdf2872e4f901398260db`
- Max submit arithmetic: BOOTSTRAP_RERUN_ALLOWANCE = 1; MAX_POSSIBLE_CAMPAIGN_B_SUBMITS = 762; conservative bound 809; MAX_ALLOWED_SUBMITS = 810
- Quota at freeze (read-only 2026-10-07T10:23:08.207657Z): allocation 120000 s, remaining 117202 s, hard cap = 0.0203 of allocation; backend operational True (active), pending 94, fixed support executable True
- Tests: {"pre_freeze_full_suite_working_tree": "169 passed, 1 skipped (live opt-in) in 414.60 s; exit 0", "post_commit_full_suite_from_committed_tree_fccb712c": "169 passed, 1 skipped (live opt-in) in 429.87 s; exit 0", "campaign_b_tests_included": "tests/campaign_b: smoke, 13 runner scenarios, 8 termination/commitment tests, 33 unit tests", "campaign_a_tests": "114 unchanged", "static_verifiers": "Campaign A immutability pass; secret scan pass; commitment verification pass; budget coherence pass; frozen-hash candidates 44/44 match; dry-run manifest C14 112/112 match; git diff --cached --check clean; LF endings only"}
- Campaign B QPU jobs submitted: 0. Acquisition status: NOT STARTED.

Tag annotation:

```
object fccb712c34f40a647f7d3b2d6171b4f2d48ba082
type commit
tag paper25b-prereg-v1
tagger Roberto <contact omitted in journal export> 1791369464 +0200

Campaign B prospective confirmatory preregistration (paper-2.5b-campaign-b), design v1.

No Campaign B QPU job was submitted before this freeze (Campaign B QPU submits = 0).

freeze_timestamp_utc: 2026-10-07T10:29:48Z
freeze_commit: fccb712c34f40a647f7d3b2d6171b4f2d48ba082
preregistration_sha256 (manuscript/PREREGISTRATION_B_v1.md): 1e02a38be3f3d1f489d17148b5c1afbf0a63517d69ccb83ff85c22c26e251e79
frozen_candidate_list: 44 files; listing_sha256: a919ea7b6192c93a2515de9e7b83d6a52ebe5a29f6c845c72dd774337ea68742
assignment_digest: 6ce29dc6d8306916cd611d3e94d17cb6cd97da43b2edce994a23e0b3cda8fae8
bootstrap_ordering_digest: fbc4b67a3ea8dcc7c2b76d8079f9937ecfffba8972011972d25b24d0a9081fb9
acquisition_commitment_digest: f193ac9114270e0a32d2d9a5b94605e9f888db021e28f43972500210e658b25c
campaign_a_immutable_tree_sha1 (artifacts/confirmatory/campaign): 83fdbaa8336e3bd4aaeacc31e6f41a395206496a
job_hard_cap: 810 submitted jobs
qpu_time_hard_cap: 2430 s (conservative 3 s/job)
target_usable_transition_windows: 10
candidate_epoch_cap: 16

This tag is immutable and is never moved. Scientifically relevant corrections require a
prospective amendment tag paper25b-prereg-v1-amendN with prior evidence preserved.
```
