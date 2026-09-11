"""One IBM QPU connectivity smoke test; never scientific evidence."""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

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
    safe_usage,
    validate_no_secret_values,
    write_pilot_json,
    write_pilot_manifest,
)
from athena_aegis.policies import AssuranceInput, P4OOSAbstention
from athena_aegis.providers import CountsResult, SubmissionRequest, select_pilot_backend
from athena_aegis.providers.ibm_runtime import IBMRuntimeAdapter


OUTPUT = Path("artifacts/pilot/connectivity_smoke.json")
SHOTS = 32


def _provider_evidence(context):
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


def _failure_payload(exc: Exception, *, submitted: bool, job_pseudonym: str | None):
    return {
        "schema_version": "athena-aegis.qpu-smoke/1.0.0",
        "phase": "pilot",
        "scientific_evidence": False,
        "experiment_type": "CONNECTIVITY_SMOKE_TEST",
        "evidence_label": "NOT_SCIENTIFIC_EVIDENCE",
        "submitted": submitted,
        "job_success": False,
        "job_id_pseudonym": job_pseudonym,
        "failure_category": type(exc).__name__,
        "sanitized_error": "smoke execution failed; provider message suppressed",
        "captured_at": utc_now(),
    }


def run() -> dict:
    if OUTPUT.exists():
        raise RuntimeError("connectivity smoke artifact already exists; refusing a duplicate QPU job")
    config = load_local_ibm_config()
    previous_disable = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    handle = None
    submitted = False
    try:
        from qiskit import QuantumCircuit
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
        selection = select_pilot_backend(adapter.list_backends(), required_qubits=1)
        if selection.selected.backend_id != config.selected_backend:
            raise RuntimeError("frozen backend selection no longer matches the eligible backend")
        pre_context = adapter.get_backend_context(config.selected_backend)
        usage_before = safe_usage(service)

        circuit = QuantumCircuit(1)
        circuit.h(0)
        circuit.measure_all()
        software_digest = sha256_digest({"qiskit": "2.5.2", "qiskit_ibm_runtime": "0.49.0"})
        request = SubmissionRequest(
            (circuit,),
            SHOTS,
            backend_id=config.selected_backend,
            transpiler_seed=19062026,
            optimization_level=0,
            context_metadata={
                "workload_id": "connectivity-smoke-v1",
                "circuit_semantic_hash": sha256_digest("one-qubit-hadamard-measure-v1"),
                "observable_definition": "single classical-bit counts",
                "software_environment_digest": software_digest,
                "calibration_window_id": "pilot-smoke-2026-09-11",
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
        counts = dict(raw.get_counts())
        if sum(counts.values()) != SHOTS:
            raise ValueError("normalized counts do not sum to requested shots")
        context = adapter.capture_execution_evidence(handle, request)
        context_schema = __import__("json").loads(
            Path("schemas/execution-context.v1.schema.json").read_text(encoding="utf-8")
        )
        Draft202012Validator(context_schema, format_checker=FormatChecker()).validate(context.to_dict())
        support = ExactStrataSupport(("backend_id", "workload_id")).fit([context]).evaluate(context)
        decision = P4OOSAbstention().decide(
            AssuranceInput(True, CalibrationState.VALID, support)
        )
        enforced = EnforcementEngine().enforce(decision, {"type": "smoke"}, counts)
        timestamp = utc_now()
        probabilities = {key: value / SHOTS for key, value in counts.items()}
        envelope = EvidenceEnvelope(
            execution_context=context,
            input_identity={"input": "fixed-one-qubit-smoke"},
            workload_identity={"workload_id": "connectivity-smoke-v1"},
            circuit_semantic_identity={"digest": request.context_metadata["circuit_semantic_hash"]},
            transpiled_identity={"digest": context.value("transpiled_circuit_hash")},
            provider_reported_evidence=_provider_evidence(context),
            raw_result_digest=sha256_digest(counts),
            postprocessed_result_digest=sha256_digest(probabilities),
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
        ).seal(HMACSHA256Signer(config.signing_key))
        if not envelope.verify_digest() or not envelope.verify_signature(
            HMACSHA256Signer(config.signing_key)
        ):
            raise RuntimeError("canonical evidence envelope verification failed")
        payload = {
            "schema_version": "athena-aegis.qpu-smoke/1.0.0",
            "phase": "pilot",
            "scientific_evidence": False,
            "experiment_type": "CONNECTIVITY_SMOKE_TEST",
            "evidence_label": "NOT_SCIENTIFIC_EVIDENCE",
            "submitted": True,
            "job_success": status.upper() == "DONE",
            "backend": config.selected_backend,
            "shots": SHOTS,
            "job_id_pseudonym": handle.job_id_pseudonym,
            "status": status,
            "result_normalized": True,
            "counts": counts,
            "timing": {
                "submit_started_at": submit_started,
                "accepted_at": accepted_at,
                "result_received_at": result_received_at,
                "wall_clock_seconds": wall_seconds,
            },
            "usage_before": usage_before,
            "usage_after": safe_usage(service),
            "backend_selection": {
                "rule": selection.rule,
                "candidates": [item.__dict__ for item in selection.candidates],
                "selected": selection.selected.backend_id,
            },
            "pre_execution_context": pre_context.to_dict(),
            "execution_context": context.to_dict(),
            "metadata_missingness": context_missingness(context),
            "envelope": envelope.to_dict(),
            "context_captured": True,
            "envelope_captured": True,
            "secret_sanitization": "pass",
        }
        validate_no_secret_values(payload, config)
        write_pilot_json(OUTPUT, payload)
        write_pilot_manifest()
        return payload
    except Exception as exc:
        payload = _failure_payload(
            exc,
            submitted=submitted,
            job_pseudonym=None if handle is None else handle.job_id_pseudonym,
        )
        validate_no_secret_values(payload, config)
        write_pilot_json(OUTPUT, payload)
        write_pilot_manifest()
        return payload
    finally:
        logging.disable(previous_disable)


def main() -> None:
    payload = run()
    print("submitted=" + ("yes" if payload["submitted"] else "no"))
    print("job_success=" + ("pass" if payload["job_success"] else "fail"))
    print("scientific_evidence=false")
    if not payload["job_success"]:
        print("failure_category=" + str(payload.get("failure_category", "unknown")))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
