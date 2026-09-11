"""Local Qiskit Aer adapter for development without QPU quota."""

from __future__ import annotations

import hashlib
import uuid
from typing import Any

from athena_aegis.canonical import sha256_digest
from athena_aegis.context import ExecutionContext, make_execution_context, pseudonymize_identifier
from athena_aegis.providers.base import BackendSummary, ProviderAdapter, ProviderJobHandle, SubmissionRequest, transpiled_circuit_digest


class SimulatorAdapter(ProviderAdapter):
    def __init__(self, *, seed_simulator: int = 19062026, pseudonym_key: bytes | None = None) -> None:
        self.seed_simulator = seed_simulator
        self._pseudonym_key = pseudonym_key or hashlib.sha256(
            b"athena-aegis-simulator-nonsecret-test-key"
        ).digest()
        self._jobs: dict[str, tuple[Any, Any]] = {}

    @staticmethod
    def _imports() -> tuple[Any, Any]:
        try:
            from qiskit import transpile
            from qiskit_aer import AerSimulator
        except ImportError as exc:
            raise RuntimeError("install the 'quantum' extra to use SimulatorAdapter") from exc
        return transpile, AerSimulator

    def list_backends(self) -> list[BackendSummary]:
        return [BackendSummary("local", "aer_simulator", True, 0, None, True, "local")]

    def get_backend_context(self, backend_id: str = "aer_simulator") -> ExecutionContext:
        if backend_id != "aer_simulator":
            raise ValueError(f"unknown simulator backend: {backend_id}")
        return make_execution_context(
            local={"provider": "local", "backend_id": backend_id, "backend_family": "AerSimulator"},
            derived={"coupling_target_digest": sha256_digest({"target": "all-to-all-simulator"})},
        )

    def submit(self, request: SubmissionRequest) -> ProviderJobHandle:
        transpile, simulator_type = self._imports()
        simulator = simulator_type(seed_simulator=self.seed_simulator)
        circuits = list(request.circuits)
        compiled = circuits if request.already_transpiled else transpile(
            circuits,
            simulator,
            seed_transpiler=request.transpiler_seed,
            optimization_level=request.optimization_level,
        )
        job = simulator.run(compiled, shots=request.shots, seed_simulator=self.seed_simulator)
        raw_id = getattr(job, "job_id", lambda: str(uuid.uuid4()))()
        pseudonym = pseudonymize_identifier(str(raw_id), self._pseudonym_key)
        self._jobs[pseudonym] = (job, compiled)
        return ProviderJobHandle("local", "aer_simulator", pseudonym, job)

    def status(self, handle: ProviderJobHandle) -> str:
        return str(handle.raw_job.status())

    def result(self, handle: ProviderJobHandle) -> Any:
        return handle.raw_job.result()

    def capture_execution_evidence(
        self, handle: ProviderJobHandle, request: SubmissionRequest
    ) -> ExecutionContext:
        _, compiled = self._jobs[handle.job_id_pseudonym]
        transpiled_digest = transpiled_circuit_digest(compiled)
        layouts = [
            _layout.final_index_layout()
            for circuit in compiled
            if (_layout := getattr(circuit, "layout", None)) is not None
        ]
        qubits = sorted({value for layout in layouts for value in layout}) if layouts else None
        return make_execution_context(
            local={
                **dict(request.context_metadata),
                "provider": "local",
                "backend_id": handle.backend_id,
                "backend_family": "AerSimulator",
                "job_id": handle.job_id_pseudonym,
                "shots": request.shots,
                "transpiler_seed": request.transpiler_seed,
                "optimization_level": request.optimization_level,
                "transpiler_name": "qiskit.transpile",
                "runtime_primitive": "AerSimulator.run",
                "runtime_configuration": dict(request.runtime_options),
                "transpiled_circuit_hash": transpiled_digest,
                **({"layout": layouts, "qubit_subset": qubits} if layouts else {}),
            },
            derived={"coupling_target_digest": sha256_digest({"target": "all-to-all-simulator"})},
            unavailable_note="not applicable to local simulator or not captured",
        )
