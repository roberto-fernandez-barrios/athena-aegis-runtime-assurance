"""P0--P5 policy ladder and exact executable action vocabulary."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from athena_aegis.calibration import CalibrationState
from athena_aegis.oos import SupportDecision


class Action(str, Enum):
    ALLOW = "ALLOW"
    HOLD = "HOLD"
    RERUN = "RERUN"
    RECALIBRATE = "RECALIBRATE"
    FALLBACK = "FALLBACK"
    ROLLBACK = "ROLLBACK"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class AssuranceInput:
    calibrated_accept: bool | None
    calibration_state: CalibrationState
    support: SupportDecision | None
    binding_valid: bool = True
    previous_release_available: bool = False
    fallback_available: bool = True
    rerun_available: bool = True


@dataclass(frozen=True)
class PolicyDecision:
    policy_id: str
    state: str
    action: Action
    reasons: tuple[str, ...]


class AssurancePolicy(ABC):
    policy_id: str

    @abstractmethod
    def decide(self, evidence: AssuranceInput) -> PolicyDecision: ...

    def _decision(self, state: str, action: Action, *reasons: str) -> PolicyDecision:
        return PolicyDecision(self.policy_id, state, action, tuple(reasons))


class P0ServeAlways(AssurancePolicy):
    policy_id = "P0-serve-always"

    def decide(self, evidence: AssuranceInput) -> PolicyDecision:
        return self._decision("UNASSESSED", Action.ALLOW, "policy serves regardless of evidence")


class P1LogOnly(AssurancePolicy):
    policy_id = "P1-context-logging-only"

    def decide(self, evidence: AssuranceInput) -> PolicyDecision:
        return self._decision("LOGGED", Action.ALLOW, "context recorded; no enforcement")


class P2GlobalCalibrated(AssurancePolicy):
    policy_id = "P2-global-calibrated"

    def decide(self, evidence: AssuranceInput) -> PolicyDecision:
        if evidence.calibration_state is not CalibrationState.VALID:
            return self._decision(evidence.calibration_state.value, Action.HOLD, "global calibration invalid")
        return self._decision("ACCEPT" if evidence.calibrated_accept else "REJECT", Action.ALLOW if evidence.calibrated_accept else Action.HOLD, "global context-agnostic threshold")


class P3ContextConditioned(P2GlobalCalibrated):
    policy_id = "P3-context-conditioned"

    def decide(self, evidence: AssuranceInput) -> PolicyDecision:
        if evidence.support is None:
            return self._decision("CALIBRATION_INVALID", Action.HOLD, "context stratum was not evaluated")
        # P3 conditions thresholds but does not add an explicit OOS decision.
        return super().decide(evidence)


class P4OOSAbstention(P3ContextConditioned):
    policy_id = "P4-context-oos-abstention"

    def decide(self, evidence: AssuranceInput) -> PolicyDecision:
        if evidence.support is None or not evidence.support.is_supported:
            reason = "context support unavailable" if evidence.support is None else evidence.support.reason
            return self._decision(CalibrationState.CONTEXT_OOS.value, Action.HOLD, reason, "abstain before calibrated assurance")
        return super().decide(evidence)


class P5RecoveryEnforcement(P4OOSAbstention):
    policy_id = "P5-recovery-enforcement"

    def decide(self, evidence: AssuranceInput) -> PolicyDecision:
        if not evidence.binding_valid:
            return self._decision("INTEGRITY_FAILURE", Action.BLOCK, "authenticated evaluation binding failed")
        base = super().decide(evidence)
        if base.action is Action.HOLD:
            if base.state in (CalibrationState.CONTEXT_OOS.value, CalibrationState.CALIBRATION_INVALID.value):
                return self._decision(base.state, Action.RECALIBRATE, *base.reasons)
            if base.state == "REJECT" and evidence.rerun_available:
                return self._decision(base.state, Action.RERUN, *base.reasons)
            if evidence.fallback_available:
                return self._decision(base.state, Action.FALLBACK, *base.reasons)
            if evidence.previous_release_available:
                return self._decision(base.state, Action.ROLLBACK, *base.reasons)
            return self._decision(base.state, Action.HOLD, *base.reasons)
        return base
