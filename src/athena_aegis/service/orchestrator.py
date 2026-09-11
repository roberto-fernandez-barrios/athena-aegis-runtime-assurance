"""Minimal executable AEGIS slice of an HSaaS/FMS request path."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from athena_aegis.enforcement import EnforcementEngine, EnforcementOutcome
from athena_aegis.policies import AssuranceInput, AssurancePolicy, PolicyDecision


@dataclass(frozen=True)
class ServiceOutcome:
    decision: PolicyDecision
    enforcement: EnforcementOutcome
    service_correctness: float | None


class HSaaSOrchestrator:
    """request -> preparation -> quantum result -> assurance -> recovery -> response."""

    def __init__(self, policy: AssurancePolicy, enforcement: EnforcementEngine) -> None:
        self.policy = policy
        self.enforcement = enforcement

    def complete(
        self,
        *,
        request: Any,
        candidate_result: Any,
        assurance: AssuranceInput,
        correctness_oracle: Callable[[Any], float] | None = None,
    ) -> ServiceOutcome:
        decision = self.policy.decide(assurance)
        enforced = self.enforcement.enforce(decision, request, candidate_result)
        correctness = None
        if enforced.served and correctness_oracle is not None:
            correctness = float(correctness_oracle(enforced.result))
        return ServiceOutcome(decision, enforced, correctness)
