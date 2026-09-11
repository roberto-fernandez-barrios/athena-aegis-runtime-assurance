"""Execute the four-job, non-confirmatory IBM QPU pilot exactly once."""

from __future__ import annotations

import json
import logging
import statistics
import time
from pathlib import Path
from typing import Any

from athena_aegis.calibration import CalibrationState
from athena_aegis.canonical import sha256_digest, utc_now
from athena_aegis.enforcement import EnforcementEngine
from athena_aegis.evidence import (
    DecisionRecord,
    EnforcementRecord,
    EvidenceEnvelope,
    HMACSHA256Signer,
    RecoveryRecord,
)
from athena_aegis.oos import ExactStrataSupport
from athena_aegis.pilot import (
    context_missingness,
    load_local_ibm_config,
    oracle_metrics,
    repeat_discrepancy,
    safe_usage,
    validate_no_secret_values,
    write_pilot_json,
    write_pilot_manifest,
)
from athena_aegis.policies import AssuranceInput, P4OOSAbstention
from athena_aegis.providers import CountsResult, SubmissionRequest, select_pilot_backend
from athena_aegis.providers.ibm_runtime import IBMRuntimeAdapter
from athena_aegis.workloads.kernel import KernelInstance, QuantumKernelRegressionWorkload


OUTPUT = Path("artifacts/pilot/qpu_pilot_runs.json")
SMOKE = Path("artifacts/pilot/connectivity_smoke.json")
CONFIG = Path("configs/pilot.v1.json")


def _smoke_gate() -> None:
    if not SMOKE.is_file():
        raise RuntimeError("connectivity smoke artifact is absent")
    smoke = json.loads(SMOKE.read_text(encoding="utf-8"))
    required = {
        "phase": "pilot",
        "scientific_evidence": False,
        "submitted": True,
        "job_success": True,
        "result_normalized": True,
        "context_captured": True,
        "envelope_captured": True,
        "secret_sanitization": "pass",
    }
    if any(smoke.get(name) != value for name, value in required.items()):
        raise RuntimeError("connectivity smoke gate did not pass")


def _provider_evidence(context) -> dict[str, Any]:
    names = (
        "backend_calibration_timestamp",
        "t1_summary",
        "t2_summary",
        "readout_error_summary",
        "gate_error_summary",
        "queue_metadata",
        "scheduling_metadata",
    )
    return {name: context.value(name) for name in names if context.value(name) is not None}


def _write_state(payload: dict[str, Any], config) -> None:
    validate_no_secret_values(payload, config)
    write_pilot_json(OUTPUT, payload)
    write_pilot_manifest()


def _summarize(runs: list[dict[str, Any]], shot_levels: list[int]) -> dict[str, Any]:
    successful = [run for run in runs if run.get("job_success")]
    by_shots: dict[str, Any] = {}
    repeat: dict[str, Any] = {}
    for shots in shot_levels:
        group = [run for run in successful if run["shots"] == shots]
        if group:
            by_shots[str(shots)] = {
                "successful_repetitions": len(group),
                "mean_relative_frobenius_error": statistics.fmean(
                    run["oracle_metrics"]["relative_frobenius_error"] for run in group
                ),
                "maximum_absolute_error": max(
                    run["oracle_metrics"]["maximum_absolute_error"] for run in group
                ),
            }
        if len(group) == 2:
            repeat[str(shots)] = repeat_discrepancy(group[0]["kernel_matrix"], group[1]["kernel_matrix"])
    selected_shots = None
    for shots in sorted(shot_levels):
        summary = by_shots.get(str(shots))
        repeated = repeat.get(str(shots))
        if (
            summary
            and repeated
            and summary["successful_repetitions"] == 2
            and summary["mean_relative_frobenius_error"] <= 0.15
            and summary["maximum_absolute_error"] <= 0.20
            and repeated["relative_frobenius_discrepancy"] <= 0.15
        ):
            selected_shots = shots
            break
    return {
        "jobs_attempted": len(runs),
        "jobs_succeeded": len(successful),
        "job_failure_rate": 0.0 if not runs else (len(runs) - len(successful)) / len(runs),
        "by_shots": by_shots,
        "repeat_discrepancy": repeat,
        "shot_choice_rule": (
            "smallest shots with mean relative Frobenius error <= 0.15, maximum "
            "absolute error <= 0.20, and repeat relative Frobenius discrepancy <= 0.15"
        ),
        "recommended_shots": selected_shots,
        "shot_recommendation_status": "selected" if selected_shots else "unresolved",
    }


def run() -> dict[str, Any]:
    if OUTPUT.exists():
        raise RuntimeError("pilot artifact already exists; refusing duplicate QPU jobs")
    _smoke_gate()
    design = json.loads(CONFIG.read_text(encoding="utf-8"))
    jobs = list(design["job_order"])
    if len(jobs) != 4 or len(jobs) > int(design["maximum_physical_jobs"]):
        raise RuntimeError("pilot job order violates the pre-execution cap")
    features = tuple(tuple(float(value) for value in row) for row in design["features"])
    config = load_local_ibm_config()
    previous_disable = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService

        service = QiskitRuntimeService(
            channel=config.channel,
            token=config.token,
            instance=config.instance,
        )
        adapter = IBMRuntimeAdapter(
            service=service,
            instance=config.instance,
            pseudonym_key=config.pseudonym_key,
        )
        selection = select_pilot_backend(
            adapter.list_backends(), required_qubits=len(features[0])
        )
        if selection.selected.backend_id != config.selected_backend:
            raise RuntimeError("frozen backend selection no longer matches the eligible backend")
        workload = QuantumKernelRegressionWorkload()
        prepared = workload.prepare(KernelInstance(features))
        usage_before = safe_usage(service)
        payload: dict[str, Any] = {
            "schema_version": "athena-aegis.qpu-pilot/1.0.0",
            "phase": "pilot",
            "scientific_evidence": False,
            "status": "running",
            "started_at": utc_now(),
            "design_digest": sha256_digest(design),
            "backend": config.selected_backend,
            "backend_selection": {
                "rule": selection.rule,
                "required_qubits": selection.required_qubits,
                "candidates": [item.__dict__ for item in selection.candidates],
                "selected": selection.selected.backend_id,
            },
            "usage_before": usage_before,
            "runs": [],
            "confirmatory_inference": False,
        }
        signer = HMACSHA256Signer(config.signing_key)
        software_digest = sha256_digest({"qiskit": "2.5.2", "qiskit_ibm_runtime": "0.49.0"})
        for index, specification in enumerate(jobs, 1):
            handle = None
            submitted = False
            try:
                pre_context = adapter.get_backend_context(config.selected_backend)
                request = SubmissionRequest(
                    prepared.circuits,
                    int(specification["shots"]),
                    backend_id=config.selected_backend,
                    transpiler_seed=int(specification["transpiler_seed"]),
                    optimization_level=int(design["optimization_level"]),
                    context_metadata={
                        "workload_id": prepared.workload_id,
                        "circuit_semantic_hash": prepared.semantic_identity["circuit_semantic_hash"],
                        "kernel_definition": "ZZFeatureMap compute-uncompute fidelity, reps=2",
                        "software_environment_digest": software_digest,
                        "dataset_workload_digest": prepared.input_identity["dataset_workload_digest"],
                        "model_reference_version": "statevector-exact-v1",
                        "calibration_window_id": f"pilot-observation-block-{specification['observation_block']}",
                    },
                )
                submit_started = utc_now()
                wall_started = time.monotonic()
                handle = adapter.submit(request)
                submitted = True
                accepted_at = utc_now()
                raw = adapter.result(handle)
                result_received_at = utc_now()
                wall_seconds = time.monotonic() - wall_started
                status = adapter.status(handle)
                if not isinstance(raw, CountsResult):
                    raise TypeError("IBM SamplerV2 result was not normalized to CountsResult")
                counts = [dict(raw.get_counts(i)) for i in range(len(prepared.circuits))]
                if any(sum(item.values()) != request.shots for item in counts):
                    raise ValueError("normalized counts do not sum to requested shots")
                context = adapter.capture_execution_evidence(handle, request)
                matrix = workload.postprocess(raw, prepared)
                metrics = oracle_metrics(matrix, prepared.classical_reference)
                accepted = (
                    metrics["relative_frobenius_error"] <= 0.15
                    and metrics["maximum_absolute_error"] <= 0.20
                )
                support = ExactStrataSupport(("backend_id", "workload_id")).fit([context]).evaluate(context)
                decision = P4OOSAbstention().decide(
                    AssuranceInput(accepted, CalibrationState.VALID, support)
                )
                enforced = EnforcementEngine().enforce(
                    decision, prepared.input_identity, matrix.tolist()
                )
                timestamp = utc_now()
                envelope = EvidenceEnvelope(
                    execution_context=context,
                    input_identity=prepared.input_identity,
                    workload_identity={"workload_id": prepared.workload_id},
                    circuit_semantic_identity=prepared.semantic_identity,
                    transpiled_identity={"digest": context.value("transpiled_circuit_hash")},
                    provider_reported_evidence=_provider_evidence(context),
                    raw_result_digest=sha256_digest(counts),
                    postprocessed_result_digest=sha256_digest(matrix),
                    decision=DecisionRecord(
                        decision.policy_id,
                        decision.state,
                        decision.action.value,
                        decision.reasons,
                    ),
                    enforcement=EnforcementRecord(
                        decision.action.value,
                        enforced.executed_action.value,
                        enforced.detail,
                        timestamp,
                        timestamp,
                        sha256_digest(enforced.detail),
                    ),
                    recovery=RecoveryRecord("none", False, None, "not required"),
                ).seal(signer)
                if not envelope.verify_digest() or not envelope.verify_signature(signer):
                    raise RuntimeError("canonical evidence envelope verification failed")
                run_record = {
                    "run_index": index,
                    "phase": "pilot",
                    "scientific_evidence": False,
                    "observation_block": int(specification["observation_block"]),
                    "submitted": True,
                    "job_success": status.upper() == "DONE",
                    "job_id_pseudonym": handle.job_id_pseudonym,
                    "backend": config.selected_backend,
                    "shots": request.shots,
                    "transpiler_seed": request.transpiler_seed,
                    "optimization_level": request.optimization_level,
                    "status": status,
                    "timing": {
                        "submit_started_at": submit_started,
                        "accepted_at": accepted_at,
                        "result_received_at": result_received_at,
                        "wall_clock_seconds": wall_seconds,
                    },
                    "counts": counts,
                    "kernel_matrix": matrix.tolist(),
                    "oracle_metrics": metrics,
                    "pre_execution_context": pre_context.to_dict(),
                    "execution_context": context.to_dict(),
                    "metadata_missingness": context_missingness(context),
                    "envelope": envelope.to_dict(),
                }
            except Exception as exc:
                run_record = {
                    "run_index": index,
                    "phase": "pilot",
                    "scientific_evidence": False,
                    "observation_block": int(specification["observation_block"]),
                    "submitted": submitted,
                    "job_success": False,
                    "job_id_pseudonym": None if handle is None else handle.job_id_pseudonym,
                    "backend": config.selected_backend,
                    "shots": int(specification["shots"]),
                    "transpiler_seed": int(specification["transpiler_seed"]),
                    "failure_category": type(exc).__name__,
                    "sanitized_error": "pilot job failed; provider message suppressed",
                    "captured_at": utc_now(),
                }
            payload["runs"].append(run_record)
            _write_state(payload, config)
            failures = sum(not run.get("job_success") for run in payload["runs"])
            if failures / len(payload["runs"]) > 0.5:
                payload["status"] = "stopped_by_failure_rule"
                break
        payload["completed_at"] = utc_now()
        payload["usage_after"] = safe_usage(service)
        payload["summary"] = _summarize(payload["runs"], list(design["shot_levels"]))
        payload["status"] = (
            "complete" if len(payload["runs"]) == 4 and payload["summary"]["job_failure_rate"] <= 0.5
            else payload.get("status", "incomplete")
        )
        payload["temporal_interpretation"] = design["temporal_interpretation"]
        _write_state(payload, config)
        return payload
    finally:
        logging.disable(previous_disable)


def main() -> None:
    try:
        payload = run()
    except Exception as exc:
        print("pilot_execution=fail")
        print("failure_category=" + type(exc).__name__)
        print("scientific_evidence=false")
        raise SystemExit(1)
    print("pilot_execution=" + ("pass" if payload["status"] == "complete" else "fail"))
    print("jobs_attempted=" + str(payload["summary"]["jobs_attempted"]))
    print("jobs_succeeded=" + str(payload["summary"]["jobs_succeeded"]))
    print("scientific_evidence=false")
    if payload["status"] != "complete":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
