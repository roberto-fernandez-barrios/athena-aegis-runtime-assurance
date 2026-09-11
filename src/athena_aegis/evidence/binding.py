"""Preventive authenticated binding of item, prediction, and evaluation label."""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass, field
from typing import Any, Iterable

from athena_aegis.canonical import canonical_bytes, sha256_digest


@dataclass(frozen=True)
class AuthenticatedBinding:
    schema_version: str
    evaluation_id: str
    item_id: str
    prediction: Any
    label: Any
    key_id: str
    mac: str

    def unsigned_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "evaluation_id": self.evaluation_id,
            "item_id": self.item_id,
            "prediction": self.prediction,
            "label": self.label,
            "key_id": self.key_id,
        }


@dataclass(frozen=True)
class AuthenticatedEvaluationBinder:
    """Binds aligned evaluation tuples before downstream aggregation."""

    secret: bytes = field(repr=False)
    key_id: str = "evaluation-binding-v1"
    schema_version: str = "athena-aegis.evaluation-binding/1.0.0"

    def __post_init__(self) -> None:
        if len(self.secret) < 32:
            raise ValueError("binding keys must contain at least 32 bytes")

    def bind(self, evaluation_id: str, item_id: str, prediction: Any, label: Any) -> AuthenticatedBinding:
        if not evaluation_id or not item_id:
            raise ValueError("evaluation_id and item_id are required")
        payload = {
            "schema_version": self.schema_version,
            "evaluation_id": evaluation_id,
            "item_id": item_id,
            "prediction": prediction,
            "label": label,
            "key_id": self.key_id,
        }
        mac = hmac.new(
            self.secret,
            b"athena-aegis-evaluation-binding-v1\x00" + canonical_bytes(payload),
            hashlib.sha256,
        ).hexdigest()
        return AuthenticatedBinding(mac=mac, **payload)

    def verify(self, binding: AuthenticatedBinding) -> bool:
        if binding.key_id != self.key_id or binding.schema_version != self.schema_version:
            return False
        expected = self.bind(
            binding.evaluation_id,
            binding.item_id,
            binding.prediction,
            binding.label,
        )
        return hmac.compare_digest(expected.mac, binding.mac)

    def batch_digest(self, bindings: Iterable[AuthenticatedBinding]) -> str:
        return sha256_digest([binding.__dict__ for binding in bindings])

