from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable

from athena_aegis.policies import Action


@dataclass(frozen=True)
class RecoveryOutcome:
    action: Action
    success: bool
    service_result: Any
    detail: str


class RecoveryStrategy(ABC):
    strategy_id: str
    action: Action

    @abstractmethod
    def execute(self, request: Any, prior_result: Any) -> RecoveryOutcome: ...


@dataclass
class CallbackRecoveryStrategy(RecoveryStrategy):
    strategy_id: str
    action: Action
    callback: Callable[[Any, Any], Any]

    def execute(self, request: Any, prior_result: Any) -> RecoveryOutcome:
        try:
            result = self.callback(request, prior_result)
            return RecoveryOutcome(self.action, True, result, "strategy completed")
        except Exception as exc:
            return RecoveryOutcome(self.action, False, None, f"strategy failed: {type(exc).__name__}")
