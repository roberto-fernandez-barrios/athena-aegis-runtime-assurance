"""Kill criteria KC-B1..KC-B9 (author decision 17).  Reported in full, never used to select an analysis."""

from __future__ import annotations

from typing import Any, Mapping

from athena_aegis.campaign_b.constants import (
    KC_B3_MINIMUM_TERMINAL_UNITS,
    KC_B3_UNBOUND_FATAL_FRACTION,
    TARGET_USABLE_TRANSITION_WINDOWS,
)

DEFINITIONS = {
    "KC-B1": "no physical evidence: no accepted window with bound, sealed, signature-verified physical units; no physical-execution claim",
    "KC-B2": f"target not reached: fewer than {TARGET_USABLE_TRANSITION_WINDOWS} usable transition windows at stop; H1-B not tested; descriptive report only",
    "KC-B3": f"binding infeasible: preflight historical-binding self-test failure is fatal; any required UNBOUND unit makes its window non-usable; campaign-level fatal when >= {int(KC_B3_UNBOUND_FATAL_FRACTION*100)}% of scientific terminal units are UNBOUND once at least {KC_B3_MINIMUM_TERMINAL_UNITS} terminal units exist",
    "KC-B4": "recovery correctness failure: any P5 served result oracle-incorrect in any accepted window, any phase; negative result published, no success claim",
    "KC-B5": "safety-gate violation on the primary population; H1-B cannot be declared regardless of X",
    "KC-B6": "service consequence not measurable: a primary P5 record lacks determinate served, oracle, assurance, served_source or T0-T3 fields; no success claim",
    "KC-B7": "provider/API semantics incompatible: status vocabulary, metrics schema or cancellation semantics differ from the frozen expectation; a probe is physically re-executed after HOLD; two DONE attempts for one unit; halt and amend",
    "KC-B8": "budget/quota: campaign hard cap or provider limit reached before the target; stop; KC-B2 follows",
    "KC-B9": "operational infeasibility: no gate-open opportunity for 30 consecutive days, or the 90-day campaign cap; stop; KC-B2 follows",
}


def unbound_fraction(scan: Mapping[str, Any]) -> dict[str, Any]:
    terminal = int(scan.get("scientific_terminal_units", 0))
    unbound = int(scan.get("unbound_units", 0))
    fraction = (unbound / terminal) if terminal else None
    fatal = terminal >= KC_B3_MINIMUM_TERMINAL_UNITS and fraction is not None and fraction >= KC_B3_UNBOUND_FATAL_FRACTION
    return {"scientific_terminal_units": terminal, "unbound_units": unbound, "unbound_fraction": fraction, "fatal": fatal}


def evaluate_kill_criteria(state: Mapping[str, Any], scan: Mapping[str, Any], *, final: bool, analysis: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """``scan`` carries outcome-blind counts gathered by the runner; ``analysis`` only at final replay."""

    accepted = list(state.get("accepted_windows", []))
    usable = [item for item in accepted if item.get("usable_transition_window") is True]
    qualifying = [item for item in accepted if int(item.get("bound_sealed_units", 0)) > 0]
    kc: dict[str, dict[str, Any]] = {}
    kc["KC-B1"] = {"state": "not_triggered" if qualifying else ("triggered" if final else "pending"), "note": f"{len(qualifying)} accepted windows with bound sealed physical units"}
    kc["KC-B2"] = {"state": ("not_triggered" if len(usable) >= TARGET_USABLE_TRANSITION_WINDOWS else "triggered") if final else "pending", "note": f"{len(usable)} usable transition windows (target {TARGET_USABLE_TRANSITION_WINDOWS})"}
    fraction = unbound_fraction(scan)
    preflight_ok = scan.get("preflight_binding_self_test_passed")
    if preflight_ok is False or fraction["fatal"]:
        b3_state = "triggered_fatal"
    elif scan.get("windows_lost_to_unbound_units", 0):
        b3_state = "triggered_window_level"
    else:
        b3_state = "not_triggered" if preflight_ok else "pending"
    kc["KC-B3"] = {"state": b3_state, "note": f"preflight self-test {'passed' if preflight_ok else ('failed' if preflight_ok is False else 'pending')}; unbound {fraction['unbound_units']}/{fraction['scientific_terminal_units']} terminal units; windows lost to unbound units: {scan.get('windows_lost_to_unbound_units', 0)}", **fraction}
    if final and analysis is not None:
        incorrect = int(analysis.get("p5_served_oracle_incorrect_any_phase", 0))
        kc["KC-B4"] = {"state": "triggered" if incorrect else "not_triggered", "note": f"{incorrect} P5 served oracle-incorrect results across accepted windows"}
        gate = analysis.get("safety_gate", {})
        kc["KC-B5"] = {"state": "not_triggered" if gate.get("safety_gate_pass") is True else "triggered", "note": f"{len(gate.get('violations', []))} safety-gate violations on the primary population"}
        missing = analysis.get("primary_records_missing_consequences", [])
        kc["KC-B6"] = {"state": "triggered" if missing else "not_triggered", "note": f"{len(missing)} primary P5 records with missing consequence fields"}
    else:
        for key in ("KC-B4", "KC-B5", "KC-B6"):
            kc[key] = {"state": "deferred_to_analysis", "note": "outcomes are not interpreted during acquisition"}
    incidents = list(scan.get("provider_semantics_incidents", []))
    kc["KC-B7"] = {"state": "triggered_fatal" if incidents else "not_triggered", "note": "; ".join(incidents) if incidents else "provider semantics consistent with the frozen expectation"}
    budget_stop = scan.get("budget_or_quota_stop")
    kc["KC-B8"] = {"state": "triggered" if budget_stop else "not_triggered", "note": str(budget_stop) if budget_stop else "caps not reached"}
    infeasible = scan.get("operational_infeasibility_stop")
    kc["KC-B9"] = {"state": "triggered" if infeasible else "not_triggered", "note": str(infeasible) if infeasible else "gate opportunities and calendar within bounds"}
    for key, value in kc.items():
        value["frozen_definition"] = DEFINITIONS[key]
    return kc
