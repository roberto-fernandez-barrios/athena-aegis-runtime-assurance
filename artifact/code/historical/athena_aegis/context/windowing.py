"""Outcome-blind identity and lifecycle rules for calibration windows."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Sequence

from athena_aegis.canonical import sha256_digest


_FORBIDDEN_KEY_PARTS = ("token", "credential", "password", "secret", "crn", "instance_id")


def _sanitize(value: Any, *, path: str = "snapshot") -> Any:
    """Return a canonical-data projection and reject local secret material."""

    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        output: dict[str, Any] = {}
        for key, item in sorted(value.items(), key=lambda pair: str(pair[0])):
            name = str(key)
            lowered = name.lower()
            if any(part in lowered for part in _FORBIDDEN_KEY_PARTS):
                raise ValueError(f"forbidden sensitive snapshot field: {path}.{name}")
            output[name] = _sanitize(item, path=f"{path}.{name}")
        return output
    if isinstance(value, (list, tuple)):
        return [_sanitize(item, path=path) for item in value]
    raise TypeError(f"snapshot value at {path} is not canonical JSON data: {type(value).__name__}")


@dataclass(frozen=True)
class SnapshotIdentity:
    """Two non-secret digests with deliberately different scientific scopes."""

    backend_snapshot_digest: str
    workload_context_digest: str


def snapshot_identity(
    provider_snapshot: Mapping[str, Any],
    workload_context_projection: Mapping[str, Any],
) -> SnapshotIdentity:
    """Digest the full observable snapshot and the workload-relevant projection.

    Summary features such as mean T1/T2 are permitted as analysis features but
    are not sufficient inputs for either identity.  Callers provide the full
    sanitized observable snapshot and an explicit relevant projection.
    """

    backend = _sanitize(provider_snapshot, path="provider_snapshot")
    workload = _sanitize(workload_context_projection, path="workload_context")
    backend_required = {"backend_id", "configuration", "properties", "target", "software_versions"}
    backend_missing = sorted(backend_required - set(backend))
    if backend_missing:
        raise ValueError(f"backend snapshot missing full-observable fields: {backend_missing}")
    properties = backend["properties"]
    if not isinstance(properties, Mapping) or not {"qubits", "gates"}.issubset(properties):
        raise ValueError("backend snapshot properties must include per-qubit and per-gate payloads; summaries alone are invalid")
    required = {
        "backend_id",
        "physical_qubits",
        "couplings_and_gates",
        "relevant_calibration_properties",
        "layout",
        "transpilation_configuration",
        "shots",
        "runtime_configuration",
        "software_versions",
    }
    missing = sorted(required - set(workload))
    if missing:
        raise ValueError(f"workload context projection missing fields: {missing}")
    return SnapshotIdentity(
        backend_snapshot_digest=sha256_digest({"provider_snapshot": backend}),
        workload_context_digest=sha256_digest({"workload_context": workload}),
    )


def _instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@dataclass(frozen=True)
class ContextPoll:
    instance_alias: str
    backend_id: str
    provider_calibration_timestamp: str
    captured_at: str
    backend_operational: bool
    identity: SnapshotIdentity
    read_only: bool = True


@dataclass(frozen=True)
class AcceptedWindow:
    window_id: str
    provider_calibration_timestamp: str
    identity: SnapshotIdentity
    instance_alias: str
    backend_id: str


@dataclass(frozen=True)
class WindowAcceptance:
    accepted: bool
    reason: str
    window: AcceptedWindow | None = None
    background_context_variation: bool = False


def evaluate_window_candidate(
    first: ContextPoll,
    second: ContextPoll,
    previous: AcceptedWindow | None = None,
    *,
    minimum_confirmation_seconds: int = 600,
    expected_backend_id: str = "ibm_basquecountry",
) -> WindowAcceptance:
    """Apply the preregistered two-poll, workload-relevant epoch predicate."""

    if first.instance_alias != "confirmatory_instance" or second.instance_alias != "confirmatory_instance":
        return WindowAcceptance(False, "confirmatory instance required")
    if not first.read_only or not second.read_only:
        return WindowAcceptance(False, "window detection must be read-only")
    if first.backend_id != second.backend_id or first.backend_id != expected_backend_id:
        return WindowAcceptance(False, "same preregistered backend required")
    if not first.backend_operational or not second.backend_operational:
        return WindowAcceptance(False, "backend not operational at both polls")
    if not first.provider_calibration_timestamp or not second.provider_calibration_timestamp:
        return WindowAcceptance(False, "provider calibration timestamp unavailable")
    elapsed = (_instant(second.captured_at) - _instant(first.captured_at)).total_seconds()
    if elapsed < minimum_confirmation_seconds:
        return WindowAcceptance(False, "confirmation polls less than 600 seconds apart")
    if first.provider_calibration_timestamp != second.provider_calibration_timestamp:
        return WindowAcceptance(False, "provider calibration timestamp changed during confirmation")
    if first.identity != second.identity:
        return WindowAcceptance(False, "snapshot was not stable across confirmation polls")
    if previous is not None:
        if _instant(second.provider_calibration_timestamp) <= _instant(previous.provider_calibration_timestamp):
            return WindowAcceptance(False, "provider calibration timestamp is not later")
        if second.identity.workload_context_digest == previous.identity.workload_context_digest:
            changed = second.identity.backend_snapshot_digest != previous.identity.backend_snapshot_digest
            return WindowAcceptance(
                False,
                "workload context unchanged; no scientific window opened",
                background_context_variation=changed,
            )
    window_id = sha256_digest({
        "instance_alias": second.instance_alias,
        "backend_id": second.backend_id,
        "provider_calibration_timestamp": second.provider_calibration_timestamp,
        "workload_context_digest": second.identity.workload_context_digest,
    })
    return WindowAcceptance(
        True,
        "accepted workload-relevant calibration epoch",
        AcceptedWindow(
            window_id,
            second.provider_calibration_timestamp,
            second.identity,
            second.instance_alias,
            second.backend_id,
        ),
    )


@dataclass
class WindowAcquisition:
    """Pre-submit digest guard; partial records remain available for audit."""

    window: AcceptedWindow
    submitted_unit_ids: list[str] = field(default_factory=list)
    incomplete: bool = False
    incomplete_reason: str | None = None

    def gate_submit(self, unit_id: str, current: ContextPoll) -> None:
        if self.incomplete:
            raise RuntimeError("window is incomplete; new submits are stopped")
        if current.instance_alias != "confirmatory_instance":
            self._stop("instance role changed")
        elif current.backend_id != self.window.backend_id:
            self._stop("backend changed")
        elif current.identity.workload_context_digest != self.window.identity.workload_context_digest:
            self._stop("workload context digest changed during acquisition")
        elif not current.backend_operational:
            self._stop("backend became non-operational")
        if self.incomplete:
            raise RuntimeError(self.incomplete_reason or "window became incomplete")
        self.submitted_unit_ids.append(unit_id)

    def _stop(self, reason: str) -> None:
        self.incomplete = True
        self.incomplete_reason = reason


def select_fixed_physical_pair(
    qubit_properties: Mapping[int, Mapping[str, float]],
    two_qubit_edges: Sequence[Mapping[str, Any]],
) -> tuple[int, int]:
    """Provider-context-only selection: first executable edge by qubit IDs.

    The result is selected once before confirmatory outcomes and must then stay
    fixed.  This function never consumes workload outcomes.
    """

    candidates: list[tuple[int, int]] = []
    for edge in two_qubit_edges:
        if edge.get("operational") is False:
            continue
        qubits = tuple(int(value) for value in edge.get("qubits", ()))
        if len(qubits) != 2 or qubits[0] == qubits[1]:
            continue
        if any(qubit not in qubit_properties for qubit in qubits):
            continue
        a, b = sorted(qubits)
        candidates.append((a, b))
    if not candidates:
        raise RuntimeError("no executable two-qubit physical support in provider context")
    return min(candidates)
