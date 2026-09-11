"""Calibration contracts that make statistical premises explicit."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from math import ceil
from typing import Any, Mapping, Sequence

import numpy as np


class CalibrationState(str, Enum):
    VALID = "VALID"
    CALIBRATION_INVALID = "CALIBRATION_INVALID"
    CONTEXT_OOS = "CONTEXT_OOS"
    UNFIT = "UNFIT"


@dataclass(frozen=True)
class CalibrationSpecification:
    calibration_population: str
    calibration_unit: str
    independence_exchangeability_assumption: str
    temporal_window: str
    context_stratum: str
    test_unit: str
    update_recalibration_rule: str
    alpha: float

    def __post_init__(self) -> None:
        if not 0 < self.alpha < 1:
            raise ValueError("alpha must be in (0, 1)")


class CalibrationModel(ABC):
    @abstractmethod
    def fit(self, nonconformity_scores: Sequence[float]) -> "CalibrationModel": ...

    @abstractmethod
    def accepts(self, nonconformity_score: float) -> bool: ...


@dataclass
class EmpiricalQuantileCalibration(CalibrationModel):
    specification: CalibrationSpecification
    threshold: float | None = field(default=None, init=False)
    sample_size: int = field(default=0, init=False)

    def fit(self, nonconformity_scores: Sequence[float]) -> "EmpiricalQuantileCalibration":
        scores = np.sort(np.asarray(nonconformity_scores, dtype=float))
        if scores.ndim != 1 or not len(scores) or not np.isfinite(scores).all():
            raise ValueError("calibration scores must be a finite nonempty vector")
        # Split-conformal finite-sample order statistic, valid only under declared premises.
        rank = min(len(scores), ceil((len(scores) + 1) * (1 - self.specification.alpha)))
        self.threshold = float(scores[rank - 1])
        self.sample_size = len(scores)
        return self

    def accepts(self, nonconformity_score: float) -> bool:
        if self.threshold is None:
            raise RuntimeError("calibration model is not fitted")
        return float(nonconformity_score) <= self.threshold


@dataclass(frozen=True)
class CalibrationDecision:
    state: CalibrationState
    accepts: bool | None
    stratum: tuple[Any, ...]
    used_global_fallback: bool
    threshold: float | None


@dataclass
class ContextConditionedCalibration:
    """Stratum-specific thresholds with an explicit P3-only global fallback."""

    specification: CalibrationSpecification
    allow_global_fallback: bool = True
    _global: EmpiricalQuantileCalibration = field(init=False, repr=False)
    _strata: dict[tuple[Any, ...], EmpiricalQuantileCalibration] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        self._global = EmpiricalQuantileCalibration(self.specification)

    def fit(self, scores_by_stratum: Mapping[tuple[Any, ...], Sequence[float]]) -> "ContextConditionedCalibration":
        if not scores_by_stratum:
            raise ValueError("at least one context stratum is required")
        self._strata = {
            tuple(stratum): EmpiricalQuantileCalibration(self.specification).fit(scores)
            for stratum, scores in scores_by_stratum.items()
        }
        self._global.fit([score for scores in scores_by_stratum.values() for score in scores])
        return self

    def evaluate(self, stratum: tuple[Any, ...], score: float) -> CalibrationDecision:
        model = self._strata.get(tuple(stratum))
        used_global = False
        if model is None:
            if not self.allow_global_fallback:
                return CalibrationDecision(CalibrationState.CONTEXT_OOS, None, tuple(stratum), False, None)
            model = self._global
            used_global = True
        if model.threshold is None:
            return CalibrationDecision(CalibrationState.UNFIT, None, tuple(stratum), used_global, None)
        return CalibrationDecision(
            CalibrationState.VALID,
            model.accepts(score),
            tuple(stratum),
            used_global,
            model.threshold,
        )
