"""Pre-result backend selection for the non-confirmatory QPU pilot."""

from __future__ import annotations

from dataclasses import dataclass
from math import inf
from typing import Sequence

from athena_aegis.providers.base import BackendSummary


PILOT_BACKEND_SELECTION_RULE = (
    "operational non-simulator with sufficient qubits; minimize provider-reported "
    "pending jobs; break ties by backend name"
)


@dataclass(frozen=True)
class BackendSelection:
    rule: str
    required_qubits: int
    candidates: tuple[BackendSummary, ...]
    eligible: tuple[BackendSummary, ...]
    selected: BackendSummary


def select_pilot_backend(
    candidates: Sequence[BackendSummary], *, required_qubits: int
) -> BackendSelection:
    """Apply the frozen least-busy rule without consulting experiment results."""

    if required_qubits < 1:
        raise ValueError("required_qubits must be positive")
    ordered_candidates = tuple(sorted(candidates, key=lambda item: item.backend_id))
    eligible = tuple(
        item
        for item in ordered_candidates
        if item.operational is True
        and not item.simulator
        and item.num_qubits is not None
        and item.num_qubits >= required_qubits
    )
    if not eligible:
        raise RuntimeError("no operational physical backend meets the pilot circuit width")
    selected = min(
        eligible,
        key=lambda item: (
            inf if item.pending_jobs is None else item.pending_jobs,
            item.backend_id,
        ),
    )
    return BackendSelection(
        PILOT_BACKEND_SELECTION_RULE,
        required_qubits,
        ordered_candidates,
        eligible,
        selected,
    )
