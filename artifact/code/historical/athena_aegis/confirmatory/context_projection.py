"""Operator implementation of the frozen workload-context projection.

This module does not change the frozen design.  It materializes, for the live
``ibm_basquecountry`` backend, the projection that
``configs/context_window_definition.v2.json`` and Preregistration Section 5
declare: backend, fixed physical qubits, the couplings/gates used by the frozen
workload on the fixed pair, their target/calibration properties, layout,
transpilation configuration, shots, runtime configuration, software versions,
workload identity, dataset digest, and circuit semantic hash.

Per-parameter provider dates are deliberately excluded from the workload
projection: they track the backend-wide ``last_update_date`` (for example the
``rz``/``reset`` entries) and would collapse the frozen distinction between a
background backend-only change and a workload-relevant change.  Calibration
timestamps remain bound by ``backend_snapshot_digest`` and by the provider
calibration timestamp of the window itself.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from importlib.metadata import version
from typing import Any, Mapping, Sequence

from athena_aegis.canonical import canonical_text, sha256_digest, utc_now
from athena_aegis.context import ContextPoll, SnapshotIdentity, snapshot_identity


BACKEND_ID = "ibm_basquecountry"
INSTANCE_ALIAS = "confirmatory_instance"
FIXED_PHYSICAL_QUBITS: tuple[int, int] = (0, 1)
FIXED_INITIAL_LAYOUT: list[int] = [0, 1]
FIXED_NATIVE_ROUTE: list[list[int]] = [[0, 1]]
TWO_QUBIT_OPERATION = "cz"
# Native operations the frozen workload uses on the fixed pair after
# transpilation at the supported (level 1) and stress (level 2) conditions.
USED_OPERATIONS: tuple[str, ...] = ("cz", "measure", "rz", "sx")
ALLOWED_TRANSPILED_OPERATIONS = frozenset(USED_OPERATIONS) | {"barrier"}
SHOTS = 128
PRIMARY_OPTIMIZATION_LEVEL = 1
STRESS_OPTIMIZATION_LEVEL = 2
TRANSPILE_SEEDS: tuple[int, int] = (19062026, 19062027)
RUNTIME_PRIMITIVE = "SamplerV2"
RUNTIME_OPTIONS: dict[str, Any] = {}
WORKLOAD_ID = "paper15-kernel-regression-v1"
DATASET_DIGEST = "003bfc8878dcf731c26d268122f260692f56fc26a6655acb82e666422665a181"
SEMANTIC_HASH = "9d2a34dbe33a9bce977e5dd2e771b988dd75230e9cc74903896bda104c10795b"
FEATURES: tuple[tuple[float, float], ...] = ((0.1, 0.2), (0.3, 0.4), (0.5, 0.6))
STRATUM_FIELDS: tuple[str, ...] = (
    "backend_id",
    "workload_context_digest",
    "circuit_semantic_hash",
    "shots",
    "optimization_level",
    "runtime_primitive",
    "runtime_primitive_version",
    "runtime_configuration",
)

PROJECTION_DEFINITION = (
    "workload_context_projection/v1: backend_id; physical_qubits [0,1]; "
    "couplings_and_gates = target instructions for operations {cz, measure, rz, sx} "
    "whose qargs are subsets of {0,1}; relevant_calibration_properties = provider "
    "property values (name/unit/value, dates excluded) for qubits 0 and 1, provider gate "
    "property values (dates excluded) for the used operations on {0,1}, and target "
    "instruction duration/error for those operations; layout [0,1]; transpilation "
    "configuration {initial_layout [0,1], optimization_level 1, seed_transpiler_set "
    "[19062026, 19062027], transpiler qiskit.transpile}; shots 128; runtime "
    "configuration {primitive SamplerV2, options {}}; software versions {python, qiskit, "
    "qiskit_ibm_runtime, numpy}; workload_id; dataset_workload_digest; circuit_semantic_hash."
)
PROJECTION_DEFINITION_DIGEST = sha256_digest(PROJECTION_DEFINITION)


def software_versions() -> dict[str, str]:
    return {
        "python": sys.version.split()[0],
        "qiskit": version("qiskit"),
        "qiskit_ibm_runtime": version("qiskit-ibm-runtime"),
        "numpy": version("numpy"),
    }


def software_environment_digest() -> str:
    return sha256_digest(software_versions())


def _values_only(parameters: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Keep provider property values and units; drop per-parameter dates."""

    output = []
    for parameter in parameters:
        output.append(
            {
                "name": parameter.get("name"),
                "unit": parameter.get("unit"),
                "value": parameter.get("value"),
            }
        )
    return sorted(output, key=lambda item: str(item["name"]))


def _relevant_qubits(properties: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    qubits = properties.get("qubits") or []
    output: dict[str, list[dict[str, Any]]] = {}
    for qubit in FIXED_PHYSICAL_QUBITS:
        if qubit >= len(qubits):
            raise ValueError(f"provider snapshot lacks properties for fixed qubit {qubit}")
        output[str(qubit)] = _values_only(qubits[qubit])
    return output


def _relevant_gates(properties: Mapping[str, Any]) -> list[dict[str, Any]]:
    output = []
    for gate in properties.get("gates") or []:
        name = str(gate.get("gate"))
        qubits = [int(value) for value in (gate.get("qubits") or [])]
        if name not in USED_OPERATIONS or not qubits or not set(qubits) <= set(FIXED_PHYSICAL_QUBITS):
            continue
        output.append(
            {
                "gate": name,
                "qubits": qubits,
                "parameters": _values_only(gate.get("parameters") or []),
            }
        )
    return sorted(output, key=lambda item: (item["gate"], item["qubits"]))


def _relevant_target_instructions(target: Mapping[str, Any]) -> list[dict[str, Any]]:
    output = []
    for instruction in target.get("instructions") or []:
        operation = str(instruction.get("operation"))
        qubits = [int(value) for value in (instruction.get("qubits") or [])]
        if operation not in USED_OPERATIONS or not qubits or not set(qubits) <= set(FIXED_PHYSICAL_QUBITS):
            continue
        output.append(
            {
                "operation": operation,
                "qubits": qubits,
                "duration": instruction.get("duration"),
                "error": instruction.get("error"),
            }
        )
    return sorted(output, key=lambda item: (item["operation"], item["qubits"]))


def build_workload_context_projection(provider_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Project the sanitized observable snapshot onto the frozen workload identity."""

    properties = provider_snapshot.get("properties")
    target = provider_snapshot.get("target")
    if not isinstance(properties, Mapping) or not isinstance(target, Mapping):
        raise ValueError("provider snapshot must carry properties and target payloads")
    instructions = _relevant_target_instructions(target)
    return {
        "backend_id": str(provider_snapshot.get("backend_id")),
        "physical_qubits": list(FIXED_PHYSICAL_QUBITS),
        "couplings_and_gates": [
            {"operation": item["operation"], "qubits": item["qubits"]} for item in instructions
        ],
        "relevant_calibration_properties": {
            "qubits": _relevant_qubits(properties),
            "gates": _relevant_gates(properties),
            "target_instructions": instructions,
        },
        "layout": list(FIXED_INITIAL_LAYOUT),
        "transpilation_configuration": {
            "initial_layout": list(FIXED_INITIAL_LAYOUT),
            "optimization_level": PRIMARY_OPTIMIZATION_LEVEL,
            "seed_transpiler_set": list(TRANSPILE_SEEDS),
            "transpiler": "qiskit.transpile",
        },
        "shots": SHOTS,
        "runtime_configuration": {"primitive": RUNTIME_PRIMITIVE, "options": dict(RUNTIME_OPTIONS)},
        "software_versions": software_versions(),
        "workload_id": WORKLOAD_ID,
        "dataset_workload_digest": DATASET_DIGEST,
        "circuit_semantic_hash": SEMANTIC_HASH,
    }


@dataclass(frozen=True)
class FixedSupportCheck:
    executable: bool
    reasons: tuple[str, ...]
    two_qubit_edge_present: bool
    two_qubit_operation_supported: bool
    qubits_operational: bool
    gate_operational: bool


def check_fixed_support(provider_snapshot: Mapping[str, Any], backend: Any | None = None) -> FixedSupportCheck:
    """Provider-context-only executability check for the frozen pair/route."""

    reasons: list[str] = []
    edges = provider_snapshot.get("coupling_edges") or []
    edge_present = list(FIXED_NATIVE_ROUTE[0]) in [list(edge) for edge in edges]
    if not edge_present:
        reasons.append("fixed native route [[0,1]] absent from provider coupling edges")
    target = provider_snapshot.get("target") or {}
    supported = any(
        str(item.get("operation")) == TWO_QUBIT_OPERATION
        and [int(value) for value in item.get("qubits", [])] == list(FIXED_NATIVE_ROUTE[0])
        for item in target.get("instructions") or []
    )
    if not supported:
        reasons.append("fixed two-qubit operation not declared on the fixed pair by the provider target")
    qubits_operational = True
    gate_operational = True
    if backend is not None:
        properties = None
        try:
            properties = backend.properties(refresh=False)
        except Exception:
            properties = None
        if properties is not None:
            for qubit in FIXED_PHYSICAL_QUBITS:
                checker = getattr(properties, "is_qubit_operational", None)
                if callable(checker):
                    try:
                        if not checker(qubit):
                            qubits_operational = False
                    except Exception:
                        pass
            checker = getattr(properties, "is_gate_operational", None)
            if callable(checker):
                try:
                    if not checker(TWO_QUBIT_OPERATION, list(FIXED_PHYSICAL_QUBITS)):
                        gate_operational = False
                except Exception:
                    pass
    if not qubits_operational:
        reasons.append("a fixed physical qubit is reported non-operational")
    if not gate_operational:
        reasons.append("the fixed two-qubit gate is reported non-operational")
    return FixedSupportCheck(
        executable=not reasons,
        reasons=tuple(reasons),
        two_qubit_edge_present=edge_present,
        two_qubit_operation_supported=supported,
        qubits_operational=qubits_operational,
        gate_operational=gate_operational,
    )


@dataclass(frozen=True)
class LivePoll:
    """One read-only observation with both frozen digests and audit fields."""

    poll: ContextPoll
    provider_snapshot: Mapping[str, Any]
    workload_projection: Mapping[str, Any]
    support: FixedSupportCheck
    pending_jobs: int | None
    status_message: str | None
    refresh_note: str | None

    @property
    def identity(self) -> SnapshotIdentity:
        return self.poll.identity

    def sanitized_record(self) -> dict[str, Any]:
        return {
            "captured_at": self.poll.captured_at,
            "instance_alias": self.poll.instance_alias,
            "backend_id": self.poll.backend_id,
            "backend_operational": self.poll.backend_operational,
            "pending_jobs": self.pending_jobs,
            "status_message": self.status_message,
            "provider_calibration_timestamp": self.poll.provider_calibration_timestamp,
            "backend_snapshot_digest": self.identity.backend_snapshot_digest,
            "workload_context_digest": self.identity.workload_context_digest,
            "projection_definition_digest": PROJECTION_DEFINITION_DIGEST,
            "fixed_support_executable": self.support.executable,
            "fixed_support_reasons": list(self.support.reasons),
            "read_only": True,
            "qpu_jobs": 0,
            "refresh_note": self.refresh_note,
        }


def capture_live_poll(adapter: Any, *, backend_id: str = BACKEND_ID) -> LivePoll:
    """Take one read-only snapshot through the explicit confirmatory adapter."""

    from athena_aegis.providers.ibm_runtime import _observable_backend_snapshot

    if getattr(adapter, "instance_alias", None) != INSTANCE_ALIAS:
        raise RuntimeError("live polling requires the explicit confirmatory adapter")
    backend = adapter._backend(backend_id)
    refresh_note = None
    refresh = getattr(backend, "refresh", None)
    if callable(refresh):
        try:
            refresh()
        except Exception as exc:  # sanitized: provider message never retained
            refresh_note = f"refresh failed: {type(exc).__name__}"
    status = None
    try:
        status = backend.status()
    except Exception as exc:
        refresh_note = (refresh_note or "") + f"; status failed: {type(exc).__name__}"
    provider_snapshot = _observable_backend_snapshot(backend)
    projection = build_workload_context_projection(provider_snapshot)
    identity = snapshot_identity(provider_snapshot, projection)
    calibration = provider_snapshot.get("properties", {}).get("last_update_date")
    operational = bool(getattr(status, "operational", False)) if status is not None else False
    poll = ContextPoll(
        instance_alias=adapter.instance_alias,
        backend_id=str(provider_snapshot.get("backend_id")),
        provider_calibration_timestamp=str(calibration) if calibration else "",
        captured_at=utc_now(),
        backend_operational=operational,
        identity=identity,
        read_only=True,
    )
    return LivePoll(
        poll=poll,
        provider_snapshot=provider_snapshot,
        workload_projection=projection,
        support=check_fixed_support(provider_snapshot, backend),
        pending_jobs=getattr(status, "pending_jobs", None) if status is not None else None,
        status_message=getattr(status, "status_msg", None) if status is not None else None,
        refresh_note=refresh_note,
    )


class StratumView:
    """Duck-typed context view exposing exact-stratum fields to the support guard."""

    def __init__(self, fields: Mapping[str, Any], window_id: str) -> None:
        normalized = dict(fields)
        configuration = normalized.get("runtime_configuration")
        if isinstance(configuration, Mapping):
            normalized["runtime_configuration"] = canonical_text(configuration)
        normalized["calibration_window_id"] = window_id
        self._fields = normalized

    def value(self, name: str, default: Any = None) -> Any:
        return self._fields.get(name, default)

    def key(self) -> tuple[Any, ...]:
        return tuple(self._fields.get(name) for name in STRATUM_FIELDS)


def stratum_fields(
    *,
    workload_context_digest: str,
    optimization_level: int,
    runtime_primitive_version: str,
) -> dict[str, Any]:
    return {
        "backend_id": BACKEND_ID,
        "workload_context_digest": workload_context_digest,
        "circuit_semantic_hash": SEMANTIC_HASH,
        "shots": SHOTS,
        "optimization_level": int(optimization_level),
        "runtime_primitive": RUNTIME_PRIMITIVE,
        "runtime_primitive_version": runtime_primitive_version,
        "runtime_configuration": dict(RUNTIME_OPTIONS),
    }


def verify_transpiled_support(circuits: Sequence[Any]) -> dict[str, Any]:
    """Enforce the frozen execution rule on transpiled circuits before submit."""

    layouts = []
    operations: set[str] = set()
    two_qubit_pairs: set[tuple[int, ...]] = set()
    for circuit in circuits:
        layout = getattr(circuit, "layout", None)
        final = None if layout is None else list(layout.final_index_layout())
        layouts.append(final)
        for instruction in circuit.data:
            name = instruction.operation.name
            operations.add(name)
            if len(instruction.qubits) == 2 and name != "barrier":
                two_qubit_pairs.add(tuple(sorted(circuit.find_bit(q).index for q in instruction.qubits)))
    problems = []
    if any(final != FIXED_INITIAL_LAYOUT for final in layouts):
        problems.append("final index layout is not the fixed layout [0,1]")
    if not operations <= ALLOWED_TRANSPILED_OPERATIONS:
        problems.append(f"transpiled operations outside the frozen native set: {sorted(operations - ALLOWED_TRANSPILED_OPERATIONS)}")
    if two_qubit_pairs and two_qubit_pairs != {tuple(FIXED_PHYSICAL_QUBITS)}:
        problems.append(f"two-qubit operations leave the fixed pair: {sorted(two_qubit_pairs)}")
    return {
        "ok": not problems,
        "problems": problems,
        "layouts": layouts,
        "operations": sorted(operations),
        "two_qubit_pairs": sorted(two_qubit_pairs),
    }
