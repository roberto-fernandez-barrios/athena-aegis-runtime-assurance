import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from athena_aegis.canonical import sha256_digest, utc_now
from athena_aegis.context import EvidenceOrigin, EvidenceValue, make_execution_context
from athena_aegis.evidence import (
    AuthenticatedEvaluationBinder,
    DecisionRecord,
    EnforcementRecord,
    EvidenceEnvelope,
    HMACSHA256Signer,
    RecoveryRecord,
)


def test_total_context_and_schema_validation():
    context = make_execution_context(
        local={"provider": "local", "backend_id": "sim", "shots": 128},
        provider={"queue_metadata": {"pending_jobs": 2}},
        derived_untrusted={"coupling_target_digest": sha256_digest("target")},
    )
    schema = json.loads(Path("schemas/execution-context.v1.schema.json").read_text())
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(context.to_dict())
    assert len(context.fields) == 37
    assert context.fields["queue_metadata"].origin is EvidenceOrigin.PROVIDER_REPORTED
    assert context.fields["layout"].origin is EvidenceOrigin.UNAVAILABLE


def test_provider_evidence_cannot_be_marked_trusted():
    with pytest.raises(ValueError, match="provider-reported"):
        EvidenceValue("value", EvidenceOrigin.PROVIDER_REPORTED, "trusted_local")


def test_binding_detects_prediction_or_label_substitution():
    binder = AuthenticatedEvaluationBinder(b"b" * 32)
    binding = binder.bind("evaluation-1", "item-7", 1, 1)
    assert binder.verify(binding)
    corrupted = type(binding)(**{**binding.__dict__, "label": 0})
    assert not binder.verify(corrupted)


def test_envelope_canonical_seal_and_local_signature():
    context = make_execution_context(local={"provider": "local", "backend_id": "sim"})
    now = utc_now()
    envelope = EvidenceEnvelope(
        execution_context=context,
        input_identity={"id": "input-digest"},
        workload_identity={"id": "kernel"},
        circuit_semantic_identity={"digest": sha256_digest("logical")},
        transpiled_identity={"digest": sha256_digest("compiled")},
        provider_reported_evidence={},
        raw_result_digest=sha256_digest({"counts": {"00": 5}}),
        postprocessed_result_digest=sha256_digest([[1.0]]),
        decision=DecisionRecord("P4", "SUPPORTED", "ALLOW", ("accepted",)),
        enforcement=EnforcementRecord("ALLOW", "ALLOW", "served", now, now),
        recovery=RecoveryRecord("none", False, None, "not needed"),
    )
    signer = HMACSHA256Signer(b"s" * 32)
    sealed = envelope.seal(signer)
    assert sealed.verify_digest()
    assert sealed.verify_signature(signer)
    assert b"provider-reported execution evidence" in sealed.canonical_bytes()
    assert "provider attestation" not in sealed.local_signature.limitations.split(";", 1)[0]


def test_schema_documents_are_valid_schemas():
    for name in ("execution-context.v1.schema.json", "evidence-envelope.v1.schema.json"):
        Draft202012Validator.check_schema(json.loads((Path("schemas") / name).read_text()))
