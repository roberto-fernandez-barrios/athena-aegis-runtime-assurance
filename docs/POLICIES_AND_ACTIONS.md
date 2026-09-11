# Policy and action semantics

## Policy ladder

| Policy | Context behavior | Enforcement |
|---|---|---|
| P0 serve always | none | always `ALLOW` |
| P1 provenance/context logging only | records context but makes no validity decision | always `ALLOW` |
| P2 global/context-agnostic calibrated rule | one frozen threshold; Paper 1.5-style operational baseline | `ALLOW`/`HOLD` |
| P3 context-conditioned rule | stratum-specific threshold, but no explicit OOS abstention; unseen strata use its declared global fallback | `ALLOW`/`HOLD` |
| P4 context-conditioned + OOS abstention | support evaluated before calibrated rule | unsupported context is `CONTEXT_OOS` and `HOLD` |
| P5 P4 + recovery/enforcement | P4 validity gate plus binding validation and recovery policy | executable `RERUN`/`RECALIBRATE`/`FALLBACK`/`ROLLBACK`/`HOLD`/`BLOCK` |

P2 is the explicit continuity baseline for Paper 1.5. P3 can reveal whether
conditioning alone helps. P4 isolates the incremental effect of abstention. P5
isolates recovery consequence. A pilot may remove a redundant arm before the
confirmatory preregistration is committed.

## Actions

- `ALLOW`: return the current candidate result.
- `HOLD`: return no result now; retain the request for review or a later action.
- `RERUN`: execute the same semantic workload again under the frozen rerun rule.
- `RECALIBRATE`: withhold, collect the frozen calibration unit/window, refit,
  validate support, and only then reconsider the request.
- `FALLBACK`: return the declared classical/reference implementation result and
  label its source and quality.
- `ROLLBACK`: return a result from the last frozen service/model release whose
  validity criterion still holds; this is not merely reverting code.
- `BLOCK`: terminally reject this request under the active policy.

`RERUN`, `RECALIBRATE`, `FALLBACK`, and `ROLLBACK` are requests until an
enforcement handler completes them. Failure degrades to `HOLD`. A recovery is
successful only if the independent workload oracle/reference accepts its output.
No action is called fail-closed if it serves a result under insufficient
evidence.
