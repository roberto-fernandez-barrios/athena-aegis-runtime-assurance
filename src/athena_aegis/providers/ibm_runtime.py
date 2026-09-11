"""IBM Quantum Runtime 0.49 adapter.

All IBM SDK interaction is confined here. Values returned by IBM are recorded as
provider-reported, untrusted evidence. A local snapshot or signature is not a
provider attestation.
"""

from __future__ import annotations

import statistics
from datetime import datetime
from importlib.metadata import version
from typing import Any, Iterable, Mapping

from athena_aegis.canonical import sha256_digest
from athena_aegis.context import ExecutionContext, make_execution_context, pseudonymize_identifier
from athena_aegis.providers.base import CountsResult, BackendSummary, ProviderAdapter, ProviderJobHandle, SubmissionRequest, transpiled_circuit_digest


def _safe_call(obj: Any, name: str, default: Any = None, *args: Any, **kwargs: Any) -> Any:
    member = getattr(obj, name, None)
    if member is None:
        return default
    try:
        return member(*args, **kwargs) if callable(member) else member
    except Exception:
        return default


def _summary(values: Iterable[float]) -> dict[str, float | int] | None:
    clean = [float(value) for value in values if value is not None]
    if not clean:
        return None
    return {
        "count": len(clean),
        "min": min(clean),
        "median": statistics.median(clean),
        "mean": statistics.fmean(clean),
        "max": max(clean),
    }


class IBMRuntimeAdapter(ProviderAdapter):
    """Adapter matched to qiskit-ibm-runtime 0.49.x, with dependency injection."""

    def __init__(
        self,
        *,
        service: Any | None = None,
        token: str | None = None,
        channel: str = "ibm_quantum_platform",
        instance: str | None = None,
        pseudonym_key: bytes | None = None,
    ) -> None:
        if service is None:
            try:
                from qiskit_ibm_runtime import QiskitRuntimeService
            except ImportError as exc:
                raise RuntimeError("install the 'ibm' extra to use IBMRuntimeAdapter") from exc
            service = QiskitRuntimeService(channel=channel, token=token, instance=instance)
        self.service = service
        self.instance = instance
        self._pseudonym_key = pseudonym_key
        self._jobs: dict[str, tuple[Any, list[Any]]] = {}

    def list_backends(self) -> list[BackendSummary]:
        output: list[BackendSummary] = []
        for backend in self.service.backends(instance=self.instance):
            status = _safe_call(backend, "status")
            config = _safe_call(backend, "configuration")
            output.append(
                BackendSummary(
                    provider="IBM Quantum",
                    backend_id=str(getattr(backend, "name", "unknown")),
                    operational=getattr(status, "operational", None),
                    pending_jobs=getattr(status, "pending_jobs", None),
                    num_qubits=getattr(backend, "num_qubits", getattr(config, "n_qubits", None)),
                    simulator=bool(getattr(config, "simulator", False)),
                    status_message=getattr(status, "status_msg", None),
                )
            )
        return output

    def _backend(self, backend_id: str) -> Any:
        return self.service.backend(backend_id, instance=self.instance)

    def get_backend_context(self, backend_id: str) -> ExecutionContext:
        return self._capture_backend(self._backend(backend_id), extra_local={})

    def submit(self, request: SubmissionRequest) -> ProviderJobHandle:
        if not request.backend_id:
            raise ValueError("IBM submission requires an explicit backend_id")
        if self._pseudonym_key is None:
            raise ValueError("IBM submission requires a campaign-specific pseudonym_key")
        try:
            from qiskit import transpile
            from qiskit_ibm_runtime import SamplerV2
        except ImportError as exc:
            raise RuntimeError("install qiskit and qiskit-ibm-runtime") from exc
        backend = self._backend(request.backend_id)
        circuits = list(request.circuits)
        if not request.already_transpiled:
            circuits = transpile(
                circuits,
                backend=backend,
                seed_transpiler=request.transpiler_seed,
                optimization_level=request.optimization_level,
            )
        sampler = SamplerV2(mode=backend, options=dict(request.runtime_options))
        job = sampler.run(circuits, shots=request.shots)
        raw_id = str(job.job_id())
        pseudonym = pseudonymize_identifier(raw_id, self._pseudonym_key)
        self._jobs[pseudonym] = (job, circuits)
        return ProviderJobHandle("IBM Quantum", request.backend_id, pseudonym, job)

    def status(self, handle: ProviderJobHandle) -> str:
        return str(handle.raw_job.status())

    def result(self, handle: ProviderJobHandle) -> Any:
        raw_result = handle.raw_job.result()
        normalized: list[Mapping[str, int]] = []
        try:
            for pub_result in raw_result:
                data = pub_result.data
                bit_array = next(
                    value for value in vars(data).values() if hasattr(value, "get_counts")
                )
                normalized.append(dict(bit_array.get_counts()))
        except (AttributeError, StopIteration, TypeError):
            return raw_result
        return CountsResult(tuple(normalized))

    def capture_execution_evidence(
        self, handle: ProviderJobHandle, request: SubmissionRequest
    ) -> ExecutionContext:
        _, circuits = self._jobs.get(handle.job_id_pseudonym, (handle.raw_job, []))
        layouts = [
            layout.final_index_layout()
            for circuit in circuits
            if (layout := getattr(circuit, "layout", None)) is not None
        ]
        qubits = sorted({value for layout in layouts for value in layout}) if layouts else None
        options = dict(request.runtime_options)
        local = {
            **dict(request.context_metadata),
            "job_id": handle.job_id_pseudonym,
            "shots": request.shots,
            "transpiler_seed": request.transpiler_seed,
            "optimization_level": request.optimization_level,
            "transpiler_name": "qiskit.transpile",
            "transpiler_version": version("qiskit"),
            "runtime_primitive": "SamplerV2",
            "runtime_primitive_version": version("qiskit-ibm-runtime"),
            "runtime_configuration": options,
        }
        if circuits:
            local["transpiled_circuit_hash"] = transpiled_circuit_digest(circuits)
        if layouts:
            local.update({"layout": layouts, "qubit_subset": qubits})
        for context_name, option_name in (
            ("resilience_options", "resilience"),
            ("dynamical_decoupling_options", "dynamical_decoupling"),
            ("measurement_mitigation_options", "measurement_mitigation"),
        ):
            if option_name in options:
                local[context_name] = options[option_name]
        session_id = _safe_call(handle.raw_job, "session_id")
        if session_id and self._pseudonym_key is not None:
            local["session_id"] = pseudonymize_identifier(str(session_id), self._pseudonym_key)
        metrics = _safe_call(handle.raw_job, "metrics")
        provider_extra: dict[str, Any] = {}
        if isinstance(metrics, Mapping):
            allowed = ("timestamps", "usage", "position_in_queue", "execution")
            provider_extra["scheduling_metadata"] = {
                str(key): value for key, value in metrics.items() if str(key) in allowed
            }
        return self._capture_backend(
            self._backend(handle.backend_id),
            extra_local=local,
            extra_provider=provider_extra,
        )

    def _capture_backend(
        self,
        backend: Any,
        extra_local: Mapping[str, Any],
        extra_provider: Mapping[str, Any] | None = None,
    ) -> ExecutionContext:
        config = _safe_call(backend, "configuration")
        status = _safe_call(backend, "status")
        properties = _safe_call(backend, "properties", None, refresh=False)
        target = getattr(backend, "target", None)

        t1: list[float] = []
        t2: list[float] = []
        readout: list[float] = []
        gate_errors: list[float] = []
        if properties is not None:
            for qubit in range(int(getattr(backend, "num_qubits", 0) or 0)):
                for collection, method in ((t1, "t1"), (t2, "t2"), (readout, "readout_error")):
                    value = _safe_call(properties, method, None, qubit)
                    if value is not None:
                        collection.append(float(value))
            for gate in getattr(properties, "gates", []) or []:
                value = _safe_call(properties, "gate_error", None, gate.gate, gate.qubits)
                if value is not None:
                    gate_errors.append(float(value))

        calibration_at = getattr(properties, "last_update_date", None)
        if isinstance(calibration_at, datetime):
            calibration_at = calibration_at.isoformat()
        queue = None if status is None else {
            "pending_jobs": getattr(status, "pending_jobs", None),
            "operational": getattr(status, "operational", None),
            "status_message": getattr(status, "status_msg", None),
        }
        provider = {
            "provider": "IBM Quantum",
            "backend_id": str(getattr(backend, "name", "unknown")),
            "backend_family": getattr(config, "backend_name", None),
            "backend_version": getattr(config, "backend_version", None),
            "backend_calibration_timestamp": calibration_at,
            "t1_summary": _summary(t1),
            "t2_summary": _summary(t2),
            "readout_error_summary": _summary(readout),
            "gate_error_summary": _summary(gate_errors),
            "queue_metadata": queue,
        }
        provider = {key: value for key, value in provider.items() if value is not None}
        provider.update(extra_provider or {})
        target_digest = sha256_digest({
            "operation_names": sorted(getattr(target, "operation_names", []) or []),
            "coupling_map": _safe_call(getattr(backend, "coupling_map", None), "get_edges", []),
            "num_qubits": getattr(backend, "num_qubits", None),
        })
        return make_execution_context(
            local=dict(extra_local),
            provider=provider,
            derived_untrusted={"coupling_target_digest": target_digest},
            unavailable_note="not exposed by the selected IBM Runtime API or not captured",
        )
