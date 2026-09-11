"""Small routing oracle for the AEGIS slice of the FMS demonstrator.

This is a single-vehicle routing service slice with exact verification. It is not
the consortium's complete WP5 demonstrator. QAOA construction is intentionally a
typed handoff until the pilot fixes a hardware-feasible encoding.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from athena_aegis.canonical import sha256_digest
from athena_aegis.workloads.base import PreparedWorkload, Workload


@dataclass(frozen=True)
class FMSRoutingInstance:
    instance_id: str
    coordinates: tuple[tuple[float, float], ...]
    depot: int = 0

    def __post_init__(self) -> None:
        if len(self.coordinates) < 3:
            raise ValueError("at least depot plus two stops are required")
        if not 0 <= self.depot < len(self.coordinates):
            raise ValueError("invalid depot")


@dataclass(frozen=True)
class RouteSolution:
    route: tuple[int, ...]
    cost: float
    valid: bool


@dataclass(frozen=True)
class QuantumRoutingSpecification:
    encoding: str
    binary_variables: int
    objective_digest: str
    status: str = "qaoa-circuit-pending-pilot-freeze"


def route_cost(route: Sequence[int], coordinates: Sequence[tuple[float, float]]) -> float:
    return sum(math.dist(coordinates[a], coordinates[b]) for a, b in zip(route, route[1:]))


def _route_valid(route: Sequence[int], node_count: int, depot: int) -> bool:
    return (
        len(route) == node_count + 1
        and route[0] == route[-1] == depot
        and sorted(route[:-1]) == list(range(node_count))
    )


def exact_oracle(instance: FMSRoutingInstance) -> RouteSolution:
    stops = tuple(index for index in range(len(instance.coordinates)) if index != instance.depot)
    candidates = (
        (instance.depot, *permutation, instance.depot)
        for permutation in itertools.permutations(stops)
    )
    best = min(candidates, key=lambda route: route_cost(route, instance.coordinates))
    return RouteSolution(best, route_cost(best, instance.coordinates), True)


def validate_route(route: Sequence[int], instance: FMSRoutingInstance) -> bool:
    expected = set(range(len(instance.coordinates)))
    return (
        len(route) == len(instance.coordinates) + 1
        and route[0] == instance.depot
        and route[-1] == instance.depot
        and set(route[:-1]) == expected
        and len(set(route[:-1])) == len(instance.coordinates)
    )


class FMSRoutingWorkload(Workload):
    workload_id = "aegis-fms-routing-slice-v1"

    def prepare(self, instance: FMSRoutingInstance) -> PreparedWorkload:
        reference = exact_oracle(instance)
        variables = (len(instance.coordinates) - 1) ** 2
        objective = {
            "encoding": "one-hot-position-routing-QUBO",
            "nodes": len(instance.coordinates),
            "depot": instance.depot,
            "coordinates_digest": sha256_digest(instance.coordinates),
        }
        quantum_spec = QuantumRoutingSpecification(
            "one-hot-position-routing-QUBO", variables, sha256_digest(objective)
        )
        semantic = {
            "workload_id": self.workload_id,
            "scope": "AEGIS slice of the FMS demonstrator",
            "quantum_specification": quantum_spec.__dict__,
        }
        return PreparedWorkload(
            self.workload_id,
            (),
            {
                "instance_id": instance.instance_id,
                "coordinates": instance.coordinates,
                "depot": instance.depot,
                "dataset_workload_digest": sha256_digest(instance.coordinates),
            },
            {**semantic, "circuit_semantic_hash": sha256_digest(semantic)},
            reference,
        )

    def postprocess(self, provider_result: Any, prepared: PreparedWorkload) -> RouteSolution:
        if isinstance(provider_result, RouteSolution):
            return provider_result
        if not isinstance(provider_result, Mapping) or "route" not in provider_result:
            raise TypeError("routing result must contain a route")
        route = tuple(int(value) for value in provider_result["route"])
        coordinates = prepared.input_identity["coordinates"]
        depot = int(prepared.input_identity["depot"])
        valid = _route_valid(route, len(coordinates), depot)
        cost = route_cost(route, coordinates) if valid else float("inf")
        return RouteSolution(route, cost, valid)

    def correctness(self, result: RouteSolution, prepared: PreparedWorkload) -> float:
        reference: RouteSolution = prepared.classical_reference
        coordinates = prepared.input_identity["coordinates"]
        depot = int(prepared.input_identity["depot"])
        valid = result.valid and _route_valid(result.route, len(coordinates), depot)
        actual_cost = route_cost(result.route, coordinates) if valid else float("inf")
        if not valid or not math.isfinite(actual_cost) or actual_cost < reference.cost - 1e-9:
            return 0.0
        return min(1.0, reference.cost / actual_cost)
