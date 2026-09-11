"""Policy actions become observable service effects at this boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from athena_aegis.policies import Action, PolicyDecision
from athena_aegis.recovery import RecoveryOutcome, RecoveryStrategy


@dataclass(frozen=True)
class EnforcementOutcome:
    requested_action: Action
    executed_action: Action
    served: bool
    result: Any
    recovery: RecoveryOutcome | None
    detail: str


class EnforcementEngine:
    def __init__(self, strategies: Mapping[Action, RecoveryStrategy] | None = None) -> None:
        self.strategies = dict(strategies or {})

    def enforce(self, decision: PolicyDecision, request: Any, candidate_result: Any) -> EnforcementOutcome:
        action = decision.action
        if action is Action.ALLOW:
            return EnforcementOutcome(action, action, True, candidate_result, None, "candidate served")
        if action in (Action.HOLD, Action.BLOCK):
            return EnforcementOutcome(action, action, False, None, None, "service result withheld")
        strategy = self.strategies.get(action)
        if strategy is None:
            return EnforcementOutcome(action, Action.HOLD, False, None, None, "no recovery strategy configured")
        recovery = strategy.execute(request, candidate_result)
        return EnforcementOutcome(
            action,
            action if recovery.success else Action.HOLD,
            recovery.success,
            recovery.service_result if recovery.success else None,
            recovery,
            recovery.detail,
        )
