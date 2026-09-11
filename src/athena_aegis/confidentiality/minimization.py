"""Measurable metadata minimization; no circuit-confidentiality claim."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from athena_aegis.canonical import canonical_bytes, sha256_digest


@dataclass(frozen=True)
class MetadataMinimizer:
    allowed_fields: frozenset[str]
    digest_fields: frozenset[str] = frozenset()

    def minimize(self, record: Mapping[str, Any]) -> dict[str, Any]:
        output: dict[str, Any] = {}
        for name in sorted(self.allowed_fields):
            if name not in record:
                continue
            output[name] = "sha256:" + sha256_digest(record[name]) if name in self.digest_fields else record[name]
        return output

    def byte_reduction(self, before: Mapping[str, Any], after: Mapping[str, Any]) -> float:
        initial = len(canonical_bytes(before))
        return 0.0 if initial == 0 else 1.0 - len(canonical_bytes(after)) / initial
