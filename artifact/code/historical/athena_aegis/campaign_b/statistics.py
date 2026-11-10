"""Exact window-level statistics for H1-B (author decision 3).  No SciPy dependency.

H0: pi_B <= 0.5 versus H1-B: pi_B > 0.5, exact one-sided binomial test,
n = 10 usable windows, alpha = 0.05, rejection region X >= 9.  The population
is explicitly conditioned on the frozen availability gate.
"""

from __future__ import annotations

from math import comb
from typing import Any, Sequence

from athena_aegis.campaign_b.constants import (
    PRIMARY_ALPHA,
    PRIMARY_NULL_PI,
    PRIMARY_REJECTION_MINIMUM_SUCCESSES,
    TARGET_USABLE_TRANSITION_WINDOWS,
)

POPULATION_STATEMENT = (
    "pi_B = P(window_recovery_success | genuine workload-context transition admitted by the frozen "
    "Campaign-B availability gate). X >= 9 of 10 establishes evidence against pi_B <= 0.5 under the "
    "gate-conditioned population; it does not establish population reliability >= 0.90, and makes no "
    "claim at arbitrary provider congestion states."
)


def binomial_pmf(k: int, n: int, p: float) -> float:
    if k < 0 or k > n:
        return 0.0
    return comb(n, k) * (p ** k) * ((1.0 - p) ** (n - k))


def binomial_sf(k: int, n: int, p: float) -> float:
    """P(X >= k)."""

    return sum(binomial_pmf(i, n, p) for i in range(max(k, 0), n + 1))


def binomial_cdf(k: int, n: int, p: float) -> float:
    """P(X <= k)."""

    return sum(binomial_pmf(i, n, p) for i in range(0, min(k, n) + 1))


def _solve(func, target: float, lo: float = 0.0, hi: float = 1.0, iterations: int = 200) -> float:
    """Bisection for a monotone increasing func(p) = target on [0, 1]."""

    for _ in range(iterations):
        mid = (lo + hi) / 2.0
        if func(mid) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def exact_one_sided_p_value(x: int, n: int, p0: float = PRIMARY_NULL_PI) -> float:
    return binomial_sf(x, n, p0)


def clopper_pearson(x: int, n: int, alpha: float = PRIMARY_ALPHA) -> tuple[float, float]:
    lower = 0.0 if x == 0 else _solve(lambda p: binomial_sf(x, n, p), alpha / 2.0)
    upper = 1.0 if x == n else _solve(lambda p: 1.0 - binomial_cdf(x, n, p), 1.0 - alpha / 2.0)
    return lower, upper


def one_sided_lower_bound(x: int, n: int, alpha: float = PRIMARY_ALPHA) -> float:
    return 0.0 if x == 0 else _solve(lambda p: binomial_sf(x, n, p), alpha)


def primary_window_analysis(window_outcomes: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Confirmatory decision on the usable-window outcomes (one computation, at campaign end)."""

    n = len(window_outcomes)
    successes = [item for item in window_outcomes if item.get("window_recovery_success") is True]
    x = len(successes)
    report: dict[str, Any] = {
        "role": "primary_H1_B",
        "population_statement": POPULATION_STATEMENT,
        "null_hypothesis": f"pi_B <= {PRIMARY_NULL_PI}",
        "alternative_hypothesis": f"pi_B > {PRIMARY_NULL_PI}",
        "test": "exact one-sided binomial",
        "alpha": PRIMARY_ALPHA,
        "required_usable_windows": TARGET_USABLE_TRANSITION_WINDOWS,
        "rejection_region": f"X >= {PRIMARY_REJECTION_MINIMUM_SUCCESSES} of {TARGET_USABLE_TRANSITION_WINDOWS}",
        "usable_windows": n,
        "successes": x,
        "windows": [
            {
                "candidate_id": item.get("candidate_id"),
                "label": item.get("label"),
                "window_recovery_success": item.get("window_recovery_success") is True,
                "retained_result_count": item.get("retained_result_count"),
                "fallback_count": item.get("fallback_count"),
            }
            for item in window_outcomes
        ],
    }
    if n != TARGET_USABLE_TRANSITION_WINDOWS:
        report.update({
            "status": "NOT_TESTED",
            "h1_b": "NOT TESTED / NOT ESTABLISHED",
            "reason": f"{n} usable windows != {TARGET_USABLE_TRANSITION_WINDOWS}; no reduced-n test is run",
            "exact_one_sided_p_value": None,
            "clopper_pearson_95": None,
            "one_sided_95_lower_bound": None,
            "reject_h0": False,
        })
        return report
    p_value = exact_one_sided_p_value(x, n)
    lower, upper = clopper_pearson(x, n)
    report.update({
        "status": "TESTED",
        "exact_one_sided_p_value": p_value,
        "clopper_pearson_95": [lower, upper],
        "one_sided_95_lower_bound": one_sided_lower_bound(x, n),
        "reject_h0": x >= PRIMARY_REJECTION_MINIMUM_SUCCESSES,
        "h1_b": "EVIDENCE AGAINST pi_B <= 0.5 (gate-conditioned population)" if x >= PRIMARY_REJECTION_MINIMUM_SUCCESSES else "NOT ESTABLISHED",
        "leave_one_window_out": [
            {"omitted_candidate_id": item.get("candidate_id"), "successes_among_remaining": x - (1 if item.get("window_recovery_success") is True else 0), "remaining_windows": n - 1}
            for item in window_outcomes
        ],
    })
    return report
