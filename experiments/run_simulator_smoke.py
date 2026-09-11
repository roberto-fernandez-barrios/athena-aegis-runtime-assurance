"""End-to-end simulator smoke; explicitly not scientific evidence."""

from __future__ import annotations

import json
from pathlib import Path

from athena_aegis.calibration import CalibrationState
from athena_aegis.canonical import sha256_digest, utc_now
from athena_aegis.enforcement import EnforcementEngine
from athena_aegis.evidence import DecisionRecord, EnforcementRecord, EvidenceEnvelope, RecoveryRecord
from athena_aegis.oos import ExactStrataSupport
from athena_aegis.policies import AssuranceInput, P4OOSAbstention
from athena_aegis.providers import SubmissionRequest
from athena_aegis.providers.simulator import SimulatorAdapter
from athena_aegis.workloads.kernel import KernelInstance, QuantumKernelRegressionWorkload


def main() -> None:
    workload = QuantumKernelRegressionWorkload()
    prepared = workload.prepare(KernelInstance(((0.1, 0.2), (0.3, 0.4))))
    request = SubmissionRequest(
        prepared.circuits,
        512,
        transpiler_seed=19062026,
        context_metadata={
            "workload_id": prepared.workload_id,
            "circuit_semantic_hash": prepared.semantic_identity["circuit_semantic_hash"],
            "dataset_workload_digest": prepared.input_identity["dataset_workload_digest"],
            "kernel_definition": "ZZFeatureMap compute-uncompute fidelity",
            "model_reference_version": "statevector-exact-v1",
            "calibration_window_id": "simulator-smoke-window",
        },
    )
    provider = SimulatorAdapter(seed_simulator=19062026)
    handle = provider.submit(request)
    raw = provider.result(handle)
    context = provider.capture_execution_evidence(handle, request)
    matrix = workload.postprocess(raw, prepared)
    score = workload.correctness(matrix, prepared)
    support = ExactStrataSupport(("backend_id", "workload_id")).fit([context]).evaluate(context)
    policy_decision = P4OOSAbstention().decide(AssuranceInput(score >= 0.8, CalibrationState.VALID, support))
    enforced = EnforcementEngine().enforce(policy_decision, prepared.input_identity, matrix)
    timestamp = utc_now()
    envelope = EvidenceEnvelope(
        execution_context=context,
        input_identity=prepared.input_identity,
        workload_identity={"workload_id": prepared.workload_id},
        circuit_semantic_identity=prepared.semantic_identity,
        transpiled_identity={"digest": context.value("transpiled_circuit_hash")},
        provider_reported_evidence={},
        raw_result_digest=sha256_digest([raw.get_counts(i) for i in range(len(prepared.circuits))]),
        postprocessed_result_digest=sha256_digest(matrix),
        decision=DecisionRecord(policy_decision.policy_id, policy_decision.state, policy_decision.action.value, policy_decision.reasons),
        enforcement=EnforcementRecord(policy_decision.action.value, enforced.executed_action.value, enforced.detail, timestamp, timestamp),
        recovery=RecoveryRecord("none", False, None, "not required"),
        provenance_chain=(),
    ).seal()
    output = Path("artifacts/simulator/smoke_envelope.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"scientific_evidence": False, "score": score, "envelope": envelope.to_dict()}, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
