"""Context-at-execution binding J1--J4 (author decision 9).  Fail-closed.

A DONE unit becomes ``BOUND_SEALED`` only when every check passes; otherwise it
is ``UNBOUND_AUDIT_ONLY``.  No scientific outcome is inspected before this
classification.  Provider timestamps and historical properties are
provider-reported, untrusted evidence; the binding is provider-consistent
context binding, never provider attestation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from athena_aegis.campaign_b.constants import UNIT_STATE_BOUND, UNIT_STATE_UNBOUND


def _instant(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


@dataclass
class BindingEvidence:
    provider_status: str | None
    created_at: str | None
    running_at: str | None
    finished_at: str | None
    window_workload_digest: str
    pre_submit_workload_digest: str | None
    post_result_workload_digest: str | None
    historical_available: bool
    historical_workload_digest: str | None
    historical_backend_digest: str | None
    historical_calibration_timestamp: str | None
    integrity_ok: bool
    integrity_reasons: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class BindingDecision:
    bound: bool
    state: str
    checks: dict[str, bool]
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"binding_state": self.state, "context_bound": self.bound, "checks": dict(self.checks), "reasons": list(self.reasons)}


def classify_binding(evidence: BindingEvidence) -> BindingDecision:
    reasons: list[str] = []
    checks: dict[str, bool] = {}

    # J1: provider terminal state DONE with complete, monotonic timestamps.
    created, running, finished = _instant(evidence.created_at), _instant(evidence.running_at), _instant(evidence.finished_at)
    j1 = evidence.provider_status == "DONE" and created is not None and running is not None and finished is not None and created <= running <= finished
    checks["J1_provider_done_with_monotonic_timestamps"] = j1
    if not j1:
        reasons.append("J1: provider status is not DONE or created/running/finished timestamps are missing or non-monotonic")

    # J2: local pre-submit and post-result snapshots both carry the window digest.
    j2 = (
        evidence.pre_submit_workload_digest == evidence.window_workload_digest
        and evidence.post_result_workload_digest == evidence.window_workload_digest
    )
    checks["J2_local_bracket_pre_and_post_snapshots"] = j2
    if not j2:
        reasons.append("J2: local pre-submit or post-result snapshot does not carry the window workload digest")

    # J3: historical provider snapshot at running_at projects to the window digest.
    j3 = evidence.historical_available and evidence.historical_workload_digest == evidence.window_workload_digest
    checks["J3_historical_properties_at_running_match"] = j3
    if not evidence.historical_available:
        reasons.append("J3: historical provider properties at running_at unavailable")
    elif not j3:
        reasons.append("J3: historical workload-context projection at running_at differs from the window digest")

    # J4: integrity of the result and its envelope.
    j4 = bool(evidence.integrity_ok)
    checks["J4_integrity"] = j4
    if not j4:
        reasons.append("J4: integrity failure: " + "; ".join(evidence.integrity_reasons or ["unspecified"]))

    bound = all(checks.values())
    return BindingDecision(bound, UNIT_STATE_BOUND if bound else UNIT_STATE_UNBOUND, checks, tuple(reasons))


def queue_wait_seconds(evidence: BindingEvidence) -> float | None:
    created, running = _instant(evidence.created_at), _instant(evidence.running_at)
    if created is None or running is None:
        return None
    return (running - created).total_seconds()


def execution_seconds(evidence: BindingEvidence) -> float | None:
    running, finished = _instant(evidence.running_at), _instant(evidence.finished_at)
    if running is None or finished is None:
        return None
    return (finished - running).total_seconds()
