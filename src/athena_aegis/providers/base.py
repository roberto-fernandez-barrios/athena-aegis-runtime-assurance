"""Stable provider boundary used by experiments and the HSaaS service."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from io import BytesIO
from typing import Any, Mapping, Sequence

from athena_aegis.context import ExecutionContext
from athena_aegis.canonical import sha256_bytes


@dataclass(frozen=True)
class BackendSummary:
    provider: str
    backend_id: str
    operational: bool | None
    pending_jobs: int | None
    num_qubits: int | None
    simulator: bool
    status_message: str | None = None


@dataclass(frozen=True)
class SubmissionRequest:
    circuits: Sequence[Any]
    shots: int
    backend_id: str | None = None
    runtime_options: Mapping[str, Any] = field(default_factory=dict)
    context_metadata: Mapping[str, Any] = field(default_factory=dict)
    transpiler_seed: int | None = None
    optimization_level: int = 1
    already_transpiled: bool = False

    def __post_init__(self) -> None:
        if not self.circuits:
            raise ValueError("at least one circuit is required")
        if self.shots < 1:
            raise ValueError("shots must be positive")
        if self.optimization_level not in (0, 1, 2, 3):
            raise ValueError("optimization_level must be 0..3")
        allowed = {
            "workload_id", "circuit_semantic_hash", "observable_definition",
            "kernel_definition", "software_environment_digest",
            "dataset_workload_digest", "model_reference_version", "calibration_window_id",
        }
        unknown = set(self.context_metadata) - allowed
        if unknown:
            raise ValueError(f"unsupported request context metadata: {sorted(unknown)}")


@dataclass(frozen=True)
class ProviderJobHandle:
    provider: str
    backend_id: str
    job_id_pseudonym: str
    raw_job: Any = field(repr=False, compare=False)


@dataclass(frozen=True)
class CountsResult:
    """Provider-neutral count collections for shot-based workloads."""

    counts: tuple[Mapping[str, int], ...]

    def get_counts(self, experiment: int = 0) -> Mapping[str, int]:
        return self.counts[experiment]


def transpiled_circuit_digest(circuits: Sequence[Any]) -> str:
    """Hash QPY bytes; identity only, not a semantic-equivalence proof."""

    try:
        from qiskit import qpy
    except ImportError as exc:
        raise RuntimeError("Qiskit is required to serialize circuits") from exc
    stream = BytesIO()
    qpy.dump(list(circuits), stream)
    return sha256_bytes(stream.getvalue())


class ProviderAdapter(ABC):
    """No experiment may call a provider SDK outside this boundary."""

    @abstractmethod
    def list_backends(self) -> list[BackendSummary]: ...

    @abstractmethod
    def get_backend_context(self, backend_id: str) -> ExecutionContext: ...

    @abstractmethod
    def submit(self, request: SubmissionRequest) -> ProviderJobHandle: ...

    @abstractmethod
    def status(self, handle: ProviderJobHandle) -> str: ...

    @abstractmethod
    def result(self, handle: ProviderJobHandle) -> Any: ...

    @abstractmethod
    def capture_execution_evidence(
        self, handle: ProviderJobHandle, request: SubmissionRequest
    ) -> ExecutionContext: ...
