"""Optional local signing interface.

The bundled signer is an HMAC implementation for local research deployments.
It authenticates the local capture boundary; it never turns provider-reported
metadata into provider attestation.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class SignatureRecord:
    algorithm: str
    key_id: str
    signature: str
    signer_scope: str = "local_capture_boundary"
    limitations: str = (
        "authenticates the local envelope from capture onward; does not attest "
        "provider origin or correctness"
    )


@runtime_checkable
class Signer(Protocol):
    @property
    def key_id(self) -> str: ...

    def sign(self, payload: bytes) -> SignatureRecord: ...

    def verify(self, payload: bytes, signature: SignatureRecord) -> bool: ...


@dataclass(frozen=True)
class HMACSHA256Signer:
    """Shared-secret local signer. The key is excluded from repr and evidence."""

    secret: bytes = field(repr=False)
    key_id: str = "local-hmac-v1"

    def __post_init__(self) -> None:
        if len(self.secret) < 32:
            raise ValueError("local HMAC signing keys must contain at least 32 bytes")

    def sign(self, payload: bytes) -> SignatureRecord:
        value = hmac.new(self.secret, b"athena-aegis-envelope-v1\x00" + payload, hashlib.sha256)
        return SignatureRecord("HMAC-SHA256", self.key_id, value.hexdigest())

    def verify(self, payload: bytes, signature: SignatureRecord) -> bool:
        if signature.algorithm != "HMAC-SHA256" or signature.key_id != self.key_id:
            return False
        expected = self.sign(payload)
        return hmac.compare_digest(expected.signature, signature.signature)

