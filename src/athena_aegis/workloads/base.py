from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class PreparedWorkload:
    workload_id: str
    circuits: Sequence[Any]
    input_identity: Mapping[str, Any]
    semantic_identity: Mapping[str, Any]
    classical_reference: Any


class Workload(ABC):
    @abstractmethod
    def prepare(self, instance: Any) -> PreparedWorkload: ...

    @abstractmethod
    def postprocess(self, provider_result: Any, prepared: PreparedWorkload) -> Any: ...

    @abstractmethod
    def correctness(self, result: Any, prepared: PreparedWorkload) -> float: ...
