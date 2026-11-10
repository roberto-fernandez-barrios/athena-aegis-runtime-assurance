"""Versioned execution context with explicit evidence origin and trust."""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from athena_aegis.canonical import sha256_digest, utc_now


CONTEXT_SCHEMA_VERSION = "athena-aegis.execution-context/1.0.0"

CONTEXT_FIELD_NAMES: tuple[str, ...] = (
    "provider",
    "backend_id",
    "backend_family",
    "backend_version",
    "timestamp",
    "job_id",
    "session_id",
    "shots",
    "qubit_subset",
    "layout",
    "transpiler_seed",
    "optimization_level",
    "transpiler_name",
    "transpiler_version",
    "runtime_primitive",
    "runtime_primitive_version",
    "runtime_configuration",
    "resilience_options",
    "dynamical_decoupling_options",
    "measurement_mitigation_options",
    "backend_calibration_timestamp",
    "t1_summary",
    "t2_summary",
    "readout_error_summary",
    "gate_error_summary",
    "coupling_target_digest",
    "queue_metadata",
    "scheduling_metadata",
    "workload_id",
    "circuit_semantic_hash",
    "transpiled_circuit_hash",
    "observable_definition",
    "kernel_definition",
    "software_environment_digest",
    "dataset_workload_digest",
    "model_reference_version",
    "calibration_window_id",
)


class EvidenceOrigin(str, Enum):
    LOCALLY_OBSERVED = "locally_observed"
    PROVIDER_REPORTED = "provider_reported"
    DERIVED = "derived"
    UNAVAILABLE = "unavailable"


class TrustClass(str, Enum):
    TRUSTED_LOCAL = "trusted_local"
    UNTRUSTED = "untrusted"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class EvidenceValue:
    """One context value and the semantics of how it became observable."""

    value: Any
    origin: EvidenceOrigin
    trust: TrustClass
    sources: tuple[str, ...] = field(default_factory=tuple)
    note: str | None = None

    def __post_init__(self) -> None:
        unavailable = self.origin is EvidenceOrigin.UNAVAILABLE
        if unavailable != (self.trust is TrustClass.UNAVAILABLE):
            raise ValueError("unavailable origin and trust must be declared together")
        if unavailable and self.value is not None:
            raise ValueError("unavailable evidence must carry a null value")
        if self.origin is EvidenceOrigin.PROVIDER_REPORTED and self.trust is not TrustClass.UNTRUSTED:
            raise ValueError("provider-reported data is untrusted unless separately attested")

    @classmethod
    def unavailable(cls, note: str) -> "EvidenceValue":
        return cls(None, EvidenceOrigin.UNAVAILABLE, TrustClass.UNAVAILABLE, note=note)

    @classmethod
    def local(cls, value: Any, *sources: str, note: str | None = None) -> "EvidenceValue":
        return cls(value, EvidenceOrigin.LOCALLY_OBSERVED, TrustClass.TRUSTED_LOCAL, tuple(sources), note)

    @classmethod
    def provider(cls, value: Any, *sources: str, note: str | None = None) -> "EvidenceValue":
        return cls(value, EvidenceOrigin.PROVIDER_REPORTED, TrustClass.UNTRUSTED, tuple(sources), note)

    @classmethod
    def derived(
        cls,
        value: Any,
        *sources: str,
        trusted: bool = True,
        note: str | None = None,
    ) -> "EvidenceValue":
        trust = TrustClass.TRUSTED_LOCAL if trusted else TrustClass.UNTRUSTED
        return cls(value, EvidenceOrigin.DERIVED, trust, tuple(sources), note)


@dataclass(frozen=True)
class ExecutionContext:
    """A complete declaration of context fields, including unavailable ones."""

    fields: Mapping[str, EvidenceValue]
    schema_version: str = CONTEXT_SCHEMA_VERSION
    captured_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        present = set(self.fields)
        expected = set(CONTEXT_FIELD_NAMES)
        if present != expected:
            missing = sorted(expected - present)
            extra = sorted(present - expected)
            raise ValueError(f"execution context field mismatch: missing={missing}, extra={extra}")
        if any(not isinstance(value, EvidenceValue) for value in self.fields.values()):
            raise TypeError("every context field must be an EvidenceValue")

    def value(self, name: str, default: Any = None) -> Any:
        evidence = self.fields[name]
        return default if evidence.origin is EvidenceOrigin.UNAVAILABLE else evidence.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "captured_at": self.captured_at,
            "fields": {
                name: {
                    "value": evidence.value,
                    "origin": evidence.origin.value,
                    "trust": evidence.trust.value,
                    "sources": list(evidence.sources),
                    "note": evidence.note,
                }
                for name, evidence in sorted(self.fields.items())
            },
        }

    def digest(self) -> str:
        return sha256_digest(self.to_dict())


def make_execution_context(
    *,
    local: Mapping[str, Any] | None = None,
    provider: Mapping[str, Any] | None = None,
    derived: Mapping[str, Any] | None = None,
    derived_untrusted: Mapping[str, Any] | None = None,
    unavailable_note: str = "not exposed or not captured",
) -> ExecutionContext:
    """Build a total context without fabricating unavailable provider fields."""

    groups = [local or {}, provider or {}, derived or {}, derived_untrusted or {}]
    supplied = [key for group in groups for key in group]
    unknown = sorted(set(supplied) - set(CONTEXT_FIELD_NAMES))
    if unknown:
        raise ValueError(f"unknown execution context fields: {unknown}")
    if len(supplied) != len(set(supplied)):
        raise ValueError("a context field cannot be supplied by multiple provenance groups")

    fields = {name: EvidenceValue.unavailable(unavailable_note) for name in CONTEXT_FIELD_NAMES}
    for name, value in (local or {}).items():
        fields[name] = EvidenceValue.local(value, "local_runtime")
    for name, value in (provider or {}).items():
        fields[name] = EvidenceValue.provider(value, "provider_api")
    for name, value in (derived or {}).items():
        fields[name] = EvidenceValue.derived(value, "local_derivation", trusted=True)
    for name, value in (derived_untrusted or {}).items():
        fields[name] = EvidenceValue.derived(value, "provider_api", "local_derivation", trusted=False)
    if fields["timestamp"].origin is EvidenceOrigin.UNAVAILABLE:
        fields["timestamp"] = EvidenceValue.local(utc_now(), "local_clock")
    return ExecutionContext(fields=fields)


def pseudonymize_identifier(identifier: str, local_key: bytes) -> str:
    """Return a domain-separated HMAC pseudonym; never persist the raw identifier."""

    if not identifier:
        raise ValueError("identifier cannot be empty")
    if len(local_key) < 16:
        raise ValueError("pseudonymization key must contain at least 16 bytes")
    digest = hmac.new(local_key, b"athena-aegis-id-v1\x00" + identifier.encode(), hashlib.sha256)
    return "hmac-sha256:" + digest.hexdigest()
