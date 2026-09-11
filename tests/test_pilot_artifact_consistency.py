import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from athena_aegis.canonical import sha256_digest


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_live_pilot_artifact_is_nonconfirmatory_and_exactly_four_jobs():
    pilot = load("artifacts/pilot/qpu_pilot_runs.json")
    assert pilot["phase"] == "pilot"
    assert pilot["scientific_evidence"] is False
    assert pilot["status"] == "complete"
    assert len(pilot["runs"]) == 4
    assert [run["shots"] for run in pilot["runs"]] == [128, 512, 128, 512]
    assert [run["transpiler_seed"] for run in pilot["runs"]] == [
        19062026,
        19062026,
        19062027,
        19062027,
    ]
    assert all(run["job_success"] for run in pilot["runs"])
    assert all(run["job_id_pseudonym"].startswith("hmac-sha256:") for run in pilot["runs"])
    assert all(
        run["execution_context"]["fields"]["session_id"]["value"] is None
        for run in pilot["runs"]
    )
    assert pilot["summary"]["recommended_shots"] == 128
    assert pilot["summary"]["job_failure_rate"] == 0.0


def test_counts_context_missingness_and_envelopes_are_complete():
    pilot = load("artifacts/pilot/qpu_pilot_runs.json")
    schema = load("schemas/execution-context.v1.schema.json")
    expected_missing = {
        "dynamical_decoupling_options",
        "measurement_mitigation_options",
        "observable_definition",
        "resilience_options",
        "session_id",
    }
    transpiled_hashes = set()
    for run in pilot["runs"]:
        assert len(run["counts"]) == 6
        assert all(sum(counts.values()) == run["shots"] for counts in run["counts"])
        assert set(run["metadata_missingness"]["missing_fields"]) == expected_missing
        assert run["metadata_missingness"]["missing_count"] == 5
        assert run["envelope"]["envelope_digest"]
        assert run["envelope"]["local_signature"]["algorithm"] == "HMAC-SHA256"
        envelope_payload = {
            name: value
            for name, value in run["envelope"].items()
            if name not in {"envelope_digest", "local_signature"}
        }
        assert sha256_digest(envelope_payload) == run["envelope"]["envelope_digest"]
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(
            run["execution_context"]
        )
        transpiled_hashes.add(
            run["execution_context"]["fields"]["transpiled_circuit_hash"]["value"]
        )
    assert len(transpiled_hashes) == 1


def test_smoke_and_registry_job_counts_preserve_phase_boundary():
    smoke = load("artifacts/pilot/connectivity_smoke.json")
    registry = load("experiments/registry.v1.json")
    entries = {entry["experiment_id"]: entry for entry in registry["entries"]}
    assert smoke["job_success"] and smoke["scientific_evidence"] is False
    smoke_payload = {
        name: value
        for name, value in smoke["envelope"].items()
        if name not in {"envelope_digest", "local_signature"}
    }
    assert sha256_digest(smoke_payload) == smoke["envelope"]["envelope_digest"]
    assert entries["qpu-connectivity-smoke-2026-09-11"]["qpu_jobs"] == 1
    assert entries["paper25-qpu-pilot-v1"]["qpu_jobs"] == 4
    assert entries["paper25-confirmatory-v1"]["qpu_jobs"] == 0
    assert (
        entries["paper25-confirmatory-v1"]["status"]
        == "prohibited_until_preregistration_commit"
    )
    assert "DRAFT, NOT FROZEN" in Path("manuscript/PREREGISTRATION_v1.md").read_text(
        encoding="utf-8"
    )


def test_pilot_manifest_recomputes_and_excludes_confirmatory_namespace():
    manifest = load("artifacts/pilot/manifest.v1.json")
    assert manifest["phase"] == "pilot" and manifest["scientific_evidence"] is False
    for entry in manifest["files"]:
        assert entry["path"].startswith("artifacts/pilot/")
        assert "confirmatory" not in entry["path"]
        path = Path(entry["path"])
        assert path.stat().st_size == entry["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]


def test_longitudinal_recommendation_is_candidate_not_freeze():
    candidates = load("configs/longitudinal_candidates.v1.json")
    assert candidates["candidate_windows"] == [3, 5, 8, 10]
    assert candidates["status"] == "post_pilot_recommendation_not_frozen"
    assert candidates["freeze_decision"].startswith("unresolved")
    assert candidates["shots"] == 128
