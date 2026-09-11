"""Versioned evidence envelope for an operational HSaaS execution."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, replace
from typing import Any, Mapping

from athena_aegis.canonical import canonical_bytes, sha256_digest, utc_now
from athena_aegis.context import ExecutionContext
from athena_aegis.evidence.signatures import SignatureRecord, Signer


EVIDENCE_ENVELOPE_VERSION = "athena-aegis.evidence-envelope/1.0.0"


@dataclass(frozen=True)
class DecisionRecord:
    policy_id: str
    state: str
    action: str
    reasons: tuple[str, ...]
    decided_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.reasons:
            raise ValueError("a decision record requires at least one reason")


@dataclass(frozen=True)
class EnforcementRecord:
    requested_action: str
    executed_action: str
    outcome: str
    started_at: str
    completed_at: str
    detail_digest: str | None = None


@dataclass(frozen=True)
class RecoveryRecord:
    strategy_id: str
    attempted: bool
    success: bool | None
    outcome: str
    started_at: str | None = None
    completed_at: str | None = None
    result_digest: str | None = None
    parent_envelope_digest: str | None = None


@dataclass(frozen=True)
class EvidenceEnvelope:
    """Binds identity, execution, decision, enforcement, and recovery evidence."""

    execution_context: ExecutionContext
    input_identity: Mapping[str, Any]
    workload_identity: Mapping[str, Any]
    circuit_semantic_identity: Mapping[str, Any]
    transpiled_identity: Mapping[str, Any]
    provider_reported_evidence: Mapping[str, Any]
    raw_result_digest: str
    postprocessed_result_digest: str
    decision: DecisionRecord
    enforcement: EnforcementRecord
    recovery: RecoveryRecord | None
    provenance_chain: tuple[str, ...] = field(default_factory=tuple)
    authenticated_bindings_digest: str | None = None
    schema_version: str = EVIDENCE_ENVELOPE_VERSION
    envelope_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=utc_now)
    envelope_digest: str | None = None
    local_signature: SignatureRecord | None = None
    terminology: str = "provider-reported execution evidence; not provider attestation"

    def __post_init__(self) -> None:
        for name in ("raw_result_digest", "postprocessed_result_digest"):
            value = getattr(self, name)
            if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
                raise ValueError(f"{name} must be a lowercase SHA-256 digest")

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "envelope_id": self.envelope_id,
            "created_at": self.created_at,
            "execution_context": self.execution_context.to_dict(),
            "input_identity": dict(self.input_identity),
            "workload_identity": dict(self.workload_identity),
            "circuit_semantic_identity": dict(self.circuit_semantic_identity),
            "transpiled_identity": dict(self.transpiled_identity),
            "provider_reported_evidence": dict(self.provider_reported_evidence),
            "raw_result_digest": self.raw_result_digest,
            "postprocessed_result_digest": self.postprocessed_result_digest,
            "authenticated_bindings_digest": self.authenticated_bindings_digest,
            "decision": self.decision.__dict__,
            "enforcement": self.enforcement.__dict__,
            "recovery": None if self.recovery is None else self.recovery.__dict__,
            "provenance_chain": list(self.provenance_chain),
            "terminology": self.terminology,
        }

    def seal(self, signer: Signer | None = None) -> "EvidenceEnvelope":
        digest = sha256_digest(self._payload())
        signature = None if signer is None else signer.sign(bytes.fromhex(digest))
        return replace(self, envelope_digest=digest, local_signature=signature)

    def verify_digest(self) -> bool:
        return self.envelope_digest is not None and self.envelope_digest == sha256_digest(self._payload())

    def verify_signature(self, signer: Signer) -> bool:
        return (
            self.verify_digest()
            and self.local_signature is not None
            and signer.verify(bytes.fromhex(self.envelope_digest or ""), self.local_signature)
        )

    def to_dict(self) -> dict[str, Any]:
        output = self._payload()
        output["envelope_digest"] = self.envelope_digest
        output["local_signature"] = (
            None if self.local_signature is None else self.local_signature.__dict__
        )
        return output

    def canonical_bytes(self) -> bytes:
        if not self.verify_digest():
            raise ValueError("seal and verify the envelope before serialization")
        return canonical_bytes(self.to_dict())

