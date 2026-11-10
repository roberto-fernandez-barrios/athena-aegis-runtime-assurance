"""Deterministic pre-outcome assignment generation for the confirmatory campaign."""

from __future__ import annotations

import random
from typing import Any

from athena_aegis.canonical import sha256_digest


SEED = 2509112026
TRANSPILE_SEEDS = (19062026, 19062027)
POLICY_ROTATIONS = (
    ("P2-global-calibrated", "P4-context-oos-abstention", "P5-recovery-enforcement"),
    ("P4-context-oos-abstention", "P5-recovery-enforcement", "P2-global-calibrated"),
    ("P5-recovery-enforcement", "P2-global-calibrated", "P4-context-oos-abstention"),
)


def _balanced_seeds(count: int, window_index: int) -> list[int]:
    first, second = TRANSPILE_SEEDS if window_index % 2 else tuple(reversed(TRANSPILE_SEEDS))
    return [first if index % 2 == 0 else second for index in range(count)]


def generate_assignments(seed: int = SEED) -> list[dict[str, Any]]:
    """Generate the fixed block-randomized list without outcome inputs."""

    rng = random.Random(seed)
    assignments: list[dict[str, Any]] = []
    sequence = 0
    for window_index in range(1, 11):
        window_id = f"W{window_index:02d}"
        blocks: list[tuple[str, int, str, int]] = []
        if window_index > 1:
            blocks.append(("pre_recovery_service", 6, "natural_new_epoch", 1))
        blocks.append(("calibration", 39, "supported_epoch_calibration", 1))
        blocks.append(("post_recovery_verification", 2, "supported_recovered_epoch", 1))
        blocks.append(("controlled_oos_sensitivity", 2, "optimization_level_2_stress", 2))
        for phase, count, condition, optimization_level in blocks:
            units = list(range(1, count + 1))
            seeds = _balanced_seeds(count, window_index)
            paired = list(zip(units, seeds, strict=True))
            rng.shuffle(paired)
            for block_position, (unit_number, transpiler_seed) in enumerate(paired, start=1):
                sequence += 1
                service_probe = phase != "calibration"
                rotation = POLICY_ROTATIONS[(window_index + unit_number + block_position) % len(POLICY_ROTATIONS)]
                assignments.append({
                    "sequence": sequence,
                    "window": window_id,
                    "phase": phase,
                    "block_position": block_position,
                    "unit_id": f"{window_id}-{phase}-{unit_number:02d}",
                    "condition": condition,
                    "optimization_level": optimization_level,
                    "shots": 128,
                    "transpiler_seed": transpiler_seed,
                    "policy_replay_order": list(rotation) if service_probe else [],
                    "physical_submission": True,
                })
    return assignments


def assignment_digest(assignments: list[dict[str, Any]]) -> str:
    return sha256_digest({"assignments": assignments})
