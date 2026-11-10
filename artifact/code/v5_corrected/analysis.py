# POST-CAMPAIGN v5 correction: KC-B4 blocks declaration. Not acquisition code.
"""Campaign B replay analysis on sealed evidence (zero QPU).  Outcome-blind usability first, then endpoints."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Any, Mapping, Sequence

from athena_aegis.analysis.metrics import wilson_rate
from athena_aegis.campaign_b.constants import POLICY_P2, POLICY_P4, POLICY_P5, SERVED_SOURCE_FALLBACK, SERVED_SOURCE_HELD
from athena_aegis.campaign_b.endpoints import safety_gate, window_recovery_success
from athena_aegis.campaign_b.immutability import verify_campaign_a_immutable
from athena_aegis.campaign_b.kill_criteria import evaluate_kill_criteria
from athena_aegis.campaign_b.statistics import primary_window_analysis


def _lines(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _rate(numerator: int, denominator: int, unit: str) -> dict[str, Any]:
    if denominator <= 0:
        return {"numerator": numerator, "denominator": denominator, "estimate": None, "lower": None, "upper": None, "experimental_unit": unit}
    return wilson_rate(numerator, denominator, unit).__dict__


def _quantiles(values: Sequence[float]) -> dict[str, float] | None:
    clean = sorted(float(v) for v in values if v is not None)
    if not clean:
        return None
    return {"n": len(clean), "min": clean[0], "median": median(clean), "max": clean[-1]}


def load_campaign(campaign_dir: Path) -> dict[str, Any]:
    state = json.loads((campaign_dir / "campaign_state.json").read_text(encoding="utf-8"))
    windows: dict[str, dict[str, Any]] = {}
    for directory in sorted((campaign_dir / "windows").glob("C*")):
        windows[directory.name] = {
            "window": json.loads((directory / "window.json").read_text(encoding="utf-8")),
            "units": _lines(directory / "units.jsonl"),
            "policy_records": _lines(directory / "policy_records.jsonl"),
        }
    return {"state": state, "windows": windows, "ledger": _lines(campaign_dir / "ledger.jsonl"), "late": _lines(campaign_dir / "late_results.jsonl"), "polls": _lines(campaign_dir / "polls.jsonl")}


def primary_p5_records(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [dict(r) for r in records if r.get("policy_id") == POLICY_P5 and r.get("phase") == "pre_recovery_service" and r.get("primary_contrast_eligible") is True and "recovered_valid_service" in r]


def analyze(campaign_dir: Path, *, repo_root: Path, verify_campaign_a: bool = True) -> dict[str, Any]:
    immutability = verify_campaign_a_immutable(repo_root) if verify_campaign_a else None
    data = load_campaign(campaign_dir)
    state = data["state"]
    accepted = list(state.get("accepted_windows", []))
    usable_entries = [item for item in accepted if item.get("usable_transition_window") is True]

    # Outcome-blind population first.
    window_outcomes: list[dict[str, Any]] = []
    missing_consequences: list[str] = []
    for entry in usable_entries:
        candidate = str(entry["candidate_id"])
        records = primary_p5_records(data["windows"][candidate]["policy_records"])
        for record in records:
            for field in ("served", "oracle_service_correct", "assurance_valid_for_serving", "total_recovery_latency_seconds", "context_bound"):
                if record.get(field) is None and not (field in ("oracle_service_correct", "assurance_valid_for_serving") and record.get("served") is False):
                    missing_consequences.append(f"{candidate}/{record.get('probe_id')}:{field}")
            if record.get("served") is True and record.get("served_source") not in (SERVED_SOURCE_HELD, SERVED_SOURCE_FALLBACK):
                missing_consequences.append(f"{candidate}/{record.get('probe_id')}:served_source")
        outcome = window_recovery_success(records)
        window_outcomes.append({"candidate_id": candidate, "label": entry.get("label"), **outcome})
    primary = primary_window_analysis(window_outcomes)
    gate = safety_gate([record for entry in usable_entries for record in primary_p5_records(data["windows"][str(entry["candidate_id"])]["policy_records"])])

    # Secondary and safety reports over all accepted windows.
    all_records = [record for entry in accepted for record in data["windows"][str(entry["candidate_id"])]["policy_records"]]
    p5_all = [r for r in all_records if r.get("policy_id") == POLICY_P5]
    p2_all = [r for r in all_records if r.get("policy_id") == POLICY_P2]
    usable_p5 = [record for entry in usable_entries for record in primary_p5_records(data["windows"][str(entry["candidate_id"])]["policy_records"])]
    served_usable = [r for r in usable_p5 if r.get("served") is True]
    retained = [r for r in served_usable if r.get("served_source") == SERVED_SOURCE_HELD]
    fallbacks = [r for r in served_usable if r.get("served_source") == SERVED_SOURCE_FALLBACK]
    latencies = [r.get("total_recovery_latency_seconds") for r in usable_p5 if isinstance(r.get("total_recovery_latency_seconds"), (int, float))]
    p5_incorrect_any = sum(1 for r in p5_all if r.get("served") is True and r.get("oracle_service_correct") is not True)
    units_all = [unit for entry in list(accepted) + list(state.get("incomplete_windows", [])) for unit in data["windows"][str(entry["candidate_id"])]["units"]]
    terminal_states = Counter(unit.get("terminal_state") for unit in units_all)
    queue_waits = [unit["timings"].get("provider_queue_wait_seconds") for unit in units_all if unit.get("timings", {}).get("provider_queue_wait_seconds") is not None]
    verification = [r for r in all_records if r.get("phase") == "post_recovery_verification"]
    secondary = {
        "retained_result_only_window_success": {"windows": sum(1 for w in window_outcomes if w.get("retained_result_only_success")), "usable_windows": len(window_outcomes)},
        "fallbacks": {"count": len(fallbacks), "fraction_of_served_primary_probes": _rate(len(fallbacks), len(served_usable), "served primary probe")},
        "retained_result_rate": _rate(len(retained), len(usable_p5), "primary probe"),
        "recovery_latency_T0_T3_seconds": _quantiles(latencies),
        "recalibration_latency_T1_T2_seconds": _quantiles([r.get("recalibration_latency_seconds") for r in usable_p5 if r.get("recalibration_latency_seconds") is not None]),
        "observable_provider_queue_wait_seconds": _quantiles(queue_waits),
        "service_availability": {policy: _rate(sum(1 for r in all_records if r.get("policy_id") == policy and r.get("available_correct_within_deadline") is True), sum(1 for r in all_records if r.get("policy_id") == policy), "service request") for policy in (POLICY_P2, POLICY_P4, POLICY_P5)},
        "p2_assurance_invalid_continuation": _rate(sum(1 for r in p2_all if r.get("assurance_invalid_continuation") is True and r.get("phase") == "pre_recovery_service"), sum(1 for r in p2_all if r.get("phase") == "pre_recovery_service"), "pre-recovery probe"),
        "p5_assurance_invalid_continuation": _rate(sum(1 for r in p5_all if r.get("assurance_invalid_continuation") is True), len(p5_all), "P5 record"),
        "incorrect_service_continuation": {policy: _rate(sum(1 for r in all_records if r.get("policy_id") == policy and r.get("unsafe_service_continuation") is True), sum(1 for r in all_records if r.get("policy_id") == policy and r.get("served") is True), "served result") for policy in (POLICY_P2, POLICY_P4, POLICY_P5)},
        "verification_probe_behavior": {policy: _rate(sum(1 for r in verification if r.get("policy_id") == policy and r.get("served") is True and r.get("oracle_service_correct") is True), sum(1 for r in verification if r.get("policy_id") == policy), "verification probe") for policy in (POLICY_P2, POLICY_P4, POLICY_P5)},
        "missingness": {"unit_terminal_states": dict(terminal_states), "incomplete_windows": [w.get("candidate_id") for w in state.get("incomplete_windows", [])], "accepted_non_usable": [w.get("candidate_id") for w in accepted if w.get("status") == "accepted_non_usable"], "late_results": len(data["late"])},
        "binding_failures": {"unbound_units": int(state.get("unbound_units", 0)), "scientific_terminal_units": int(state.get("scientific_terminal_units", 0)), "windows_lost_to_unbound_units": int(state.get("windows_lost_to_unbound_units", 0))},
        "post_window_terminal_results": {"in_window_units": int(state.get("post_window_terminal_results", 0)), "late_after_close": sum(1 for item in data["late"] if item.get("classification") == "post_window_terminal_result"), "promoted_to_scientific_evidence": 0},
        "queue_exposure": {"gate_statistics": state.get("gate_statistics"), "queue_depth_at_open": [w.get("queue_depth_at_open") for w in accepted], "max_queue_depth_in_window": [w.get("max_queue_depth_in_window") for w in accepted]},
        "qpu_resource_usage": {"jobs_consumed": state.get("jobs_consumed"), "qpu_seconds_consumed_estimate": state.get("qpu_seconds_consumed_estimate"), "qpu_seconds_provider_reported": state.get("qpu_seconds_provider_reported"), "cancel_requests": state.get("cancel_requests"), "acquisition_reruns": state.get("acquisition_reruns_used_total")},
    }
    analysis_scan = {"p5_served_oracle_incorrect_any_phase": p5_incorrect_any, "safety_gate": gate, "primary_records_missing_consequences": missing_consequences}
    kill = evaluate_kill_criteria(state, {
        "scientific_terminal_units": int(state.get("scientific_terminal_units", 0)), "unbound_units": int(state.get("unbound_units", 0)), "windows_lost_to_unbound_units": int(state.get("windows_lost_to_unbound_units", 0)),
        "preflight_binding_self_test_passed": state.get("preflight_binding_self_test_passed"), "provider_semantics_incidents": [i["incident"] for i in state.get("provider_semantics_incidents", [])],
        "budget_or_quota_stop": state.get("budget_or_quota_stop"), "operational_infeasibility_stop": state.get("operational_infeasibility_stop"),
    }, final=True, analysis=analysis_scan)
    # Window-level KC-B3 only removes those windows from the usable population; the declaration is blocked by
    # KC-B1, KC-B4, KC-B5, KC-B6 (triggered) and by the fatal forms of KC-B3 and KC-B7.
    fatal = [key for key, value in kill.items() if (key in ("KC-B1", "KC-B4", "KC-B5", "KC-B6") and value["state"] == "triggered") or (key in ("KC-B3", "KC-B7") and value["state"] == "triggered_fatal")]
    declared = primary.get("reject_h0") is True and gate["safety_gate_pass"] and not fatal and primary.get("status") == "TESTED"
    return {
        "schema_version": "athena-aegis.campaign-b-analysis/1.0.0",
        "campaign": state.get("campaign"),
        "phase": state.get("phase"),
        "scientific_evidence": state.get("phase") == "confirmatory",
        "qpu_jobs_submitted_by_analysis": 0,
        "generated_at": datetime.now().astimezone().isoformat(),
        "campaign_a_immutability": immutability,
        "campaign_status": state.get("campaign_status"),
        "status_reason": state.get("status_reason"),
        "population": {"candidate_epochs": state.get("candidate_epochs"), "accepted_windows": len(accepted), "usable_transition_windows": len(usable_entries), "usable_candidates": [w.get("candidate_id") for w in usable_entries], "accepted_non_usable": [w.get("candidate_id") for w in accepted if w.get("status") == "accepted_non_usable"], "bootstrap": [w.get("candidate_id") for w in accepted if w.get("status") == "accepted_bootstrap"], "incomplete": [w.get("candidate_id") for w in state.get("incomplete_windows", [])]},
        "primary": primary,
        "safety_gate": gate,
        "h1_b_declared": declared,
        "h1_b_statement": primary.get("h1_b"),
        "kill_criteria": kill,
        "secondary": secondary,
        "stale_reference_selections": [{"candidate_id": w.get("candidate_id"), **(w.get("stale_reference") or {})} for w in accepted],
    }


def write_analysis(campaign_dir: Path, output_dir: Path, *, repo_root: Path, verify_campaign_a: bool = True) -> dict[str, Any]:
    from athena_aegis.campaign_b.immutability import guard_write_path

    report = analyze(campaign_dir, repo_root=repo_root, verify_campaign_a=verify_campaign_a)
    target = guard_write_path(output_dir / "analysis.json", repo_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8", newline="\n")
    summary = [
        f"# Campaign B analysis ({report['phase']}) — scientific_evidence={report['scientific_evidence']}",
        "",
        f"Campaign status: {report['campaign_status']} ({report['status_reason']})",
        f"Population: epochs={report['population']['candidate_epochs']} accepted={report['population']['accepted_windows']} usable={report['population']['usable_transition_windows']} non-usable={report['population']['accepted_non_usable']} incomplete={report['population']['incomplete']}",
        f"Primary: status={report['primary']['status']} X={report['primary']['successes']}/{report['primary']['usable_windows']} p={report['primary'].get('exact_one_sided_p_value')} CP95={report['primary'].get('clopper_pearson_95')} LB95={report['primary'].get('one_sided_95_lower_bound')} reject_H0={report['primary'].get('reject_h0')}",
        f"Safety gate: pass={report['safety_gate']['safety_gate_pass']} violations={len(report['safety_gate']['violations'])}",
        f"H1-B declared: {report['h1_b_declared']} — {report['h1_b_statement']}",
        "",
        "| window | success | retained | fallback |",
        "|---|---|---|---|",
    ]
    for w in report["primary"]["windows"]:
        summary.append(f"| {w['label']} ({w['candidate_id']}) | {w['window_recovery_success']} | {w['retained_result_count']} | {w['fallback_count']} |")
    summary += ["", "Kill criteria: " + ", ".join(f"{k}={v['state']}" for k, v in report["kill_criteria"].items())]
    (output_dir / "analysis_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8", newline="\n")
    return report
