"""Primary endpoint, window outcome and safety gate (author decisions 2 and 4).

Every indeterminate value is fail-closed: a probe with an unknown oracle,
assurance, binding or latency never counts as recovered, and a *served*
result with an indeterminate oracle/assurance/binding is a safety violation.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from athena_aegis.campaign_b.constants import (
    MAX_FALLBACK_PROBES,
    MIN_RETAINED_RESULT_PROBES,
    PRIMARY_PROBES,
    SERVED_SOURCE_FALLBACK,
    SERVED_SOURCE_HELD,
    SERVICE_DEADLINE_SECONDS,
)


def _is_true(value: Any) -> bool:
    return value is True


def probe_recovered_valid_service(record: Mapping[str, Any]) -> dict[str, Any]:
    """Per-probe primary endpoint on a P5 policy record (fail-closed)."""

    failed: list[str] = []
    if not _is_true(record.get("context_bound")):
        failed.append("context_bound")
    if not _is_true(record.get("held_physical_result_exists")):
        failed.append("held_physical_result_exists")
    if not _is_true(record.get("served")):
        failed.append("served")
    if not _is_true(record.get("oracle_service_correct")):
        failed.append("oracle_service_correct")
    if not _is_true(record.get("assurance_valid_for_serving")):
        failed.append("assurance_valid_for_serving")
    latency = record.get("total_recovery_latency_seconds")
    if not isinstance(latency, (int, float)) or isinstance(latency, bool) or latency > SERVICE_DEADLINE_SECONDS:
        failed.append("recovery_latency_within_deadline")
    if record.get("service_probe_qpu_rerun") is not False:
        failed.append("service_probe_qpu_rerun_is_false")
    if not _is_true(record.get("trusted_invariants_held")):
        failed.append("trusted_invariants_held")
    source = record.get("served_source")
    if _is_true(record.get("served")) and source not in (SERVED_SOURCE_HELD, SERVED_SOURCE_FALLBACK):
        failed.append("served_source_known")
    return {
        "recovered_valid_service": not failed,
        "failed_conditions": failed,
        "served_source": source,
        "retained_result": _is_true(record.get("served")) and source == SERVED_SOURCE_HELD,
        "fallback": _is_true(record.get("served")) and source == SERVED_SOURCE_FALLBACK,
    }


def window_recovery_success(probe_records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Window-level outcome over the six primary held probes."""

    evaluations = [probe_recovered_valid_service(record) for record in probe_records]
    probe_ids = sorted(str(record.get("probe_id")) for record in probe_records)
    retained = sum(item["retained_result"] for item in evaluations)
    fallback = sum(item["fallback"] for item in evaluations)
    all_recovered = len(evaluations) == PRIMARY_PROBES and all(item["recovered_valid_service"] for item in evaluations)
    distinct = len(set(probe_ids)) == PRIMARY_PROBES
    success = all_recovered and distinct and retained >= MIN_RETAINED_RESULT_PROBES and fallback <= MAX_FALLBACK_PROBES
    return {
        "window_recovery_success": success,
        "probe_count": len(evaluations),
        "distinct_probes": distinct,
        "all_probes_recovered": all_recovered,
        "retained_result_count": retained,
        "fallback_count": fallback,
        "retained_result_only_success": all_recovered and distinct and retained == PRIMARY_PROBES,
        "probes": [{"probe_id": str(record.get("probe_id")), **item} for record, item in zip(probe_records, evaluations)],
    }


def safety_gate(primary_p5_records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Fail-closed safety gate over the primary P5 population."""

    violations: list[dict[str, Any]] = []
    checked = 0
    for record in primary_p5_records:
        checked += 1
        if not _is_true(record.get("served")):
            continue
        problems = []
        if record.get("oracle_service_correct") is not True:
            problems.append("served with oracle incorrect or indeterminate")
        if record.get("assurance_valid_for_serving") is not True:
            problems.append("served with invalid or indeterminate assurance")
        if record.get("context_bound") is not True:
            problems.append("served with failed or indeterminate context binding")
        if record.get("trusted_invariants_held") is not True:
            problems.append("served with failed trusted invariants")
        if problems:
            violations.append({"candidate_id": record.get("candidate_id"), "probe_id": record.get("probe_id"), "problems": problems})
    return {"safety_gate_pass": not violations, "records_checked": checked, "violations": violations}
