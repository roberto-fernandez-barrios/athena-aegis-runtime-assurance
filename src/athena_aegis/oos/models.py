"""Interpretable context-support baselines; model selection is pilot-driven."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from math import exp
from typing import Any, Mapping, Sequence

import numpy as np

from athena_aegis.context import ExecutionContext


@dataclass(frozen=True)
class SupportDecision:
    is_supported: bool
    support_score: float
    reason: str
    reference_windows: tuple[str, ...]


class ContextSupportModel(ABC):
    @abstractmethod
    def fit(self, contexts: Sequence[ExecutionContext]) -> "ContextSupportModel": ...

    @abstractmethod
    def evaluate(self, context: ExecutionContext) -> SupportDecision: ...


@dataclass
class ExactStrataSupport(ContextSupportModel):
    fields: tuple[str, ...]
    _strata: dict[tuple[Any, ...], set[str]] = field(default_factory=dict, init=False)

    def fit(self, contexts: Sequence[ExecutionContext]) -> "ExactStrataSupport":
        self._strata.clear()
        for context in contexts:
            key = tuple(context.value(name) for name in self.fields)
            window = str(context.value("calibration_window_id", "unlabeled"))
            self._strata.setdefault(key, set()).add(window)
        if not self._strata:
            raise ValueError("at least one calibration context is required")
        return self

    def evaluate(self, context: ExecutionContext) -> SupportDecision:
        key = tuple(context.value(name) for name in self.fields)
        windows = tuple(sorted(self._strata.get(key, set())))
        supported = bool(windows)
        return SupportDecision(
            supported,
            1.0 if supported else 0.0,
            "declared context stratum observed" if supported else "declared context stratum unseen",
            windows,
        )


def _numeric_vector(context: ExecutionContext, fields: Sequence[str]) -> np.ndarray:
    values: list[float] = []
    for name in fields:
        value = context.value(name)
        if isinstance(value, Mapping):
            value = value.get("mean")
        if value is None:
            raise ValueError(f"numeric context field unavailable: {name}")
        values.append(float(value))
    return np.asarray(values, dtype=float)


@dataclass
class StandardizedDistanceSupport(ContextSupportModel):
    fields: tuple[str, ...]
    maximum_distance: float = 3.0
    _mean: np.ndarray | None = field(default=None, init=False, repr=False)
    _scale: np.ndarray | None = field(default=None, init=False, repr=False)
    _windows: tuple[str, ...] = field(default=(), init=False)

    def fit(self, contexts: Sequence[ExecutionContext]) -> "StandardizedDistanceSupport":
        values = np.vstack([_numeric_vector(context, self.fields) for context in contexts])
        self._mean = values.mean(axis=0)
        scale = values.std(axis=0, ddof=1) if len(values) > 1 else np.ones(values.shape[1])
        self._scale = np.where(scale <= 1e-12, 1.0, scale)
        self._windows = tuple(sorted({str(c.value("calibration_window_id", "unlabeled")) for c in contexts}))
        return self

    def evaluate(self, context: ExecutionContext) -> SupportDecision:
        if self._mean is None or self._scale is None:
            raise RuntimeError("support model is not fitted")
        try:
            distance = float(np.linalg.norm((_numeric_vector(context, self.fields) - self._mean) / self._scale))
        except ValueError as exc:
            return SupportDecision(False, 0.0, str(exc), self._windows)
        score = max(0.0, 1.0 - distance / self.maximum_distance)
        return SupportDecision(
            distance <= self.maximum_distance,
            score,
            f"standardized context distance={distance:.6g}; threshold={self.maximum_distance:.6g}",
            self._windows,
        )


@dataclass
class DiagonalGaussianSupport(ContextSupportModel):
    fields: tuple[str, ...]
    minimum_relative_density: float = 0.01
    _distance: StandardizedDistanceSupport = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not 0 < self.minimum_relative_density < 1:
            raise ValueError("minimum_relative_density must be in (0, 1)")
        self._distance = StandardizedDistanceSupport(self.fields, maximum_distance=float("inf"))

    def fit(self, contexts: Sequence[ExecutionContext]) -> "DiagonalGaussianSupport":
        self._distance.fit(contexts)
        return self

    def evaluate(self, context: ExecutionContext) -> SupportDecision:
        base = self._distance.evaluate(context)
        try:
            distance = float(base.reason.split("=")[1].split(";")[0])
        except (IndexError, ValueError):
            return SupportDecision(False, 0.0, base.reason, base.reference_windows)
        density = exp(-0.5 * distance * distance)
        return SupportDecision(
            density >= self.minimum_relative_density,
            density,
            f"diagonal-Gaussian relative density={density:.6g}; threshold={self.minimum_relative_density:.6g}",
            base.reference_windows,
        )
