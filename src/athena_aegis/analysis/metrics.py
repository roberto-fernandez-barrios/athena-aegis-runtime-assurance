"""Endpoint estimators keep denominator and experimental unit visible."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Callable, Iterable, Mapping


@dataclass(frozen=True)
class RateEstimate:
    numerator: int
    denominator: int
    estimate: float
    lower: float
    upper: float
    experimental_unit: str
    uncertainty: str = "Wilson 95% interval"


def wilson_rate(successes: int, total: int, experimental_unit: str) -> RateEstimate:
    if not 0 <= successes <= total or total <= 0:
        raise ValueError("require 0 <= successes <= total and total > 0")
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    half = z * sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return RateEstimate(successes, total, p, max(0.0, centre - half), min(1.0, centre + half), experimental_unit)


def endpoint_rate(
    records: Iterable[Mapping[str, object]],
    *,
    denominator_filter: Callable[[Mapping[str, object]], bool],
    numerator_filter: Callable[[Mapping[str, object]], bool],
    experimental_unit: str,
) -> RateEstimate:
    eligible = [record for record in records if denominator_filter(record)]
    successes = sum(bool(numerator_filter(record)) for record in eligible)
    return wilson_rate(successes, len(eligible), experimental_unit)
