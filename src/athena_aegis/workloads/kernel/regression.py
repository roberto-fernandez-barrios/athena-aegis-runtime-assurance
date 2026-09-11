"""Paper 1.5-compatible quantum-kernel regression workload.

This independently implements the same compute-uncompute fidelity-kernel family;
it does not modify or import the frozen Paper 1.5 repository.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np

from athena_aegis.canonical import sha256_digest
from athena_aegis.workloads.base import PreparedWorkload, Workload


@dataclass(frozen=True)
class KernelInstance:
    features: tuple[tuple[float, ...], ...]
    repetitions: int = 2
    feature_map: str = "zz_feature_map"

    def array(self) -> np.ndarray:
        values = np.asarray(self.features, dtype=float)
        if values.ndim != 2 or values.shape[0] < 2 or values.shape[1] < 2:
            raise ValueError("kernel pilot requires at least 2 samples and 2 features")
        return values


def _feature_map(num_features: int, repetitions: int) -> Any:
    try:
        from qiskit.circuit.library import zz_feature_map
    except ImportError as exc:
        raise RuntimeError("install the 'quantum' extra for the kernel workload") from exc
    return zz_feature_map(num_features, reps=repetitions)


class QuantumKernelRegressionWorkload(Workload):
    workload_id = "paper15-kernel-regression-v1"

    def prepare(self, instance: KernelInstance) -> PreparedWorkload:
        try:
            from qiskit import QuantumCircuit
            from qiskit.quantum_info import Statevector
        except ImportError as exc:
            raise RuntimeError("install the 'quantum' extra for the kernel workload") from exc
        x = instance.array()
        fmap = _feature_map(x.shape[1], instance.repetitions)
        circuits: list[Any] = []
        pairs: list[tuple[int, int]] = []
        statevectors: list[Any] = []
        for row in x:
            bound = fmap.assign_parameters(row)
            statevectors.append(Statevector.from_instruction(bound))
        for i in range(len(x)):
            for j in range(i, len(x)):
                circuit = QuantumCircuit(x.shape[1])
                circuit.compose(fmap.assign_parameters(x[i]), inplace=True)
                circuit.compose(fmap.assign_parameters(x[j]).inverse(), inplace=True)
                circuit.measure_all()
                circuits.append(circuit)
                pairs.append((i, j))
        reference = np.empty((len(x), len(x)), dtype=float)
        for i in range(len(x)):
            for j in range(len(x)):
                reference[i, j] = abs(statevectors[i].inner(statevectors[j])) ** 2
        semantic = {
            "workload_id": self.workload_id,
            "feature_map": instance.feature_map,
            "repetitions": instance.repetitions,
            "num_features": x.shape[1],
            "pair_order": pairs,
        }
        return PreparedWorkload(
            self.workload_id,
            circuits,
            {"dataset_workload_digest": sha256_digest(x.tolist()), "n_samples": len(x)},
            {**semantic, "circuit_semantic_hash": sha256_digest(semantic)},
            reference,
        )

    def postprocess(self, provider_result: Any, prepared: PreparedWorkload) -> np.ndarray:
        n = int(prepared.input_identity["n_samples"])
        matrix = np.eye(n, dtype=float)
        pairs = prepared.semantic_identity["pair_order"]
        # BackendV2/Aer result interface. Runtime result normalization is adapter-level pilot work.
        for index, (i, j) in enumerate(pairs):
            counts: Mapping[str, int] = provider_result.get_counts(index)
            shots = sum(counts.values())
            probability = counts.get("0" * prepared.circuits[index].num_qubits, 0) / shots
            matrix[i, j] = matrix[j, i] = probability
        return matrix

    def correctness(self, result: np.ndarray, prepared: PreparedWorkload) -> float:
        reference = np.asarray(prepared.classical_reference)
        denominator = float(np.linalg.norm(reference, ord="fro"))
        relative_error = float(np.linalg.norm(np.asarray(result) - reference, ord="fro")) / denominator
        return max(0.0, 1.0 - relative_error)
