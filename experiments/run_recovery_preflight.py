"""Simulator/infrastructure recovery-path preflight; not scientific evidence."""

from __future__ import annotations

from pathlib import Path

from athena_aegis.canonical import sha256_digest, utc_now
from athena_aegis.context import make_execution_context
from athena_aegis.enforcement import EnforcementEngine
from athena_aegis.evidence import (
    DecisionRecord,
    EnforcementRecord,
    EvidenceEnvelope,
    RecoveryRecord,
)
from athena_aegis.pilot import write_pilot_json, write_pilot_manifest
from athena_aegis.policies import Action, PolicyDecision
from athena_aegis.recovery import CallbackRecoveryStrategy


OUTPUT = Path("artifacts/pilot/recovery_preflight.json")


def build() -> dict:
    recoverable = (Action.RERUN, Action.RECALIBRATE, Action.FALLBACK, Action.ROLLBACK)
    strategies = {
        action: CallbackRecoveryStrategy(
            "infrastructure-" + action.value.lower(),
            action,
            lambda request, prior, selected=action: {"transition": selected.value, "verified": True},
        )
        for action in recoverable
    }
    engine = EnforcementEngine(strategies)
    context = make_execution_context(
        local={
            "provider": "local-infrastructure",
            "backend_id": "recovery-preflight",
            "workload_id": "recovery-transition-v1",
            "calibration_window_id": "pilot-recovery-preflight",
        }
    )
    records = []
    for action in (Action.HOLD, *recoverable, Action.BLOCK):
        decision = PolicyDecision(
            "recovery-preflight",
            "FORCED_TEST_TRANSITION",
            action,
            ("simulator/infrastructure transition exercise",),
        )
        outcome = engine.enforce(decision, {"request": "fixed"}, {"candidate": "fixed"})
        timestamp = utc_now()
        recovery = None
        if outcome.recovery is not None:
            recovery = RecoveryRecord(
                strategies[action].strategy_id,
                True,
                outcome.recovery.success,
                outcome.recovery.detail,
                timestamp,
                timestamp,
                sha256_digest(outcome.recovery.service_result),
            )
        envelope = EvidenceEnvelope(
            execution_context=context,
            input_identity={"input": "fixed-recovery-preflight"},
            workload_identity={"workload_id": "recovery-transition-v1"},
            circuit_semantic_identity={"digest": sha256_digest("no-qpu-circuit")},
            transpiled_identity={"digest": sha256_digest("no-transpilation")},
            provider_reported_evidence={},
            raw_result_digest=sha256_digest({"candidate": "fixed"}),
            postprocessed_result_digest=sha256_digest(outcome.result),
            decision=DecisionRecord(
                decision.policy_id,
                decision.state,
                decision.action.value,
                decision.reasons,
            ),
            enforcement=EnforcementRecord(
                decision.action.value,
                outcome.executed_action.value,
                outcome.detail,
                timestamp,
                timestamp,
                sha256_digest(outcome.detail),
            ),
            recovery=recovery,
        ).seal()
        if not envelope.verify_digest():
            raise RuntimeError("recovery preflight envelope did not verify")
        records.append(
            {
                "requested_action": action.value,
                "executed_action": outcome.executed_action.value,
                "served": outcome.served,
                "recovery_attempted": outcome.recovery is not None,
                "envelope": envelope.to_dict(),
            }
        )
    return {
        "schema_version": "athena-aegis.recovery-preflight/1.0.0",
        "phase": "pilot",
        "scientific_evidence": False,
        "qpu_jobs": 0,
        "records": records,
    }


def main() -> None:
    payload = build()
    write_pilot_json(OUTPUT, payload)
    write_pilot_manifest()
    print("recovery_preflight=pass")
    print("qpu_jobs=0")


if __name__ == "__main__":
    main()
