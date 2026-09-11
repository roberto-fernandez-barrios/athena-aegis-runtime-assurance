import json
from pathlib import Path

import pytest

from athena_aegis.context import make_execution_context, pseudonymize_identifier
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


def local_config(path: Path) -> None:
    path.write_text(
        "\n".join(
            (
                "IBM_QUANTUM_API_KEY=" + "a" * 32,
                "IBM_QUANTUM_CHANNEL=ibm_quantum_platform",
                "IBM_QUANTUM_INSTANCE=" + "i" * 24,
                "ATHENA_AEGIS_SELECTED_BACKEND=fake_backend",
                "ATHENA_AEGIS_PSEUDONYM_KEY_HEX=" + "11" * 32,
                "ATHENA_AEGIS_SIGNING_KEY_HEX=" + "22" * 32,
            )
        )
        + "\n",
        encoding="utf-8",
    )


def test_local_configuration_and_pseudonymization_do_not_expose_raw_id(tmp_path):
    path = tmp_path / ".env"
    local_config(path)
    config = load_local_ibm_config(path)
    pseudonym = pseudonymize_identifier("provider-job-id", config.pseudonym_key)
    assert pseudonym.startswith("hmac-sha256:")
    assert "provider-job-id" not in pseudonym
    validate_no_secret_values({"job": pseudonym}, config)
    with pytest.raises(RuntimeError, match="secret sanitization"):
        validate_no_secret_values({"bad": config.instance}, config)


def test_oracle_and_repeat_metrics_are_predefined():
    oracle = [[1.0, 0.5], [0.5, 1.0]]
    first = [[1.0, 0.4], [0.4, 1.0]]
    second = [[1.0, 0.6], [0.6, 1.0]]
    metrics = oracle_metrics(first, oracle)
    repeat = repeat_discrepancy(first, second)
    assert metrics["relative_frobenius_error"] > 0
    assert metrics["maximum_absolute_error"] == pytest.approx(0.1)
    assert repeat["maximum_absolute_discrepancy"] == pytest.approx(0.2)


def test_provider_metadata_missingness_is_explicit():
    context = make_execution_context(
        local={"backend_id": "fake", "workload_id": "pilot"},
        provider={"queue_metadata": {"pending_jobs": 1}},
    )
    summary = context_missingness(context)
    assert summary["field_count"] == len(context.fields)
    assert "scheduling_metadata" in summary["missing_fields"]
    assert 0 < summary["missing_fraction"] < 1


def test_safe_usage_retains_numeric_quota_only():
    class Service:
        def usage(self):
            return {
                "usage_remaining_seconds": 42,
                "usage_limit_reached": False,
                "account_identifier": "private",
            }

    assert safe_usage(Service()) == {
        "usage_remaining_seconds": 42,
        "usage_limit_reached": False,
    }


def test_pilot_and_confirmatory_namespaces_are_separated(tmp_path):
    payload = {"phase": "pilot", "scientific_evidence": False, "value": 1}
    written = write_pilot_json(Path("artifacts/pilot/record.json"), payload, root=tmp_path)
    assert json.loads(written.read_text())["scientific_evidence"] is False
    assert b"\r\n" not in written.read_bytes()
    manifest = write_pilot_manifest(root=tmp_path)
    assert json.loads(manifest.read_text())["files"][0]["path"] == "artifacts/pilot/record.json"
    with pytest.raises(ValueError, match="artifacts/pilot"):
        write_pilot_json(Path("artifacts/confirmatory/bad.json"), payload, root=tmp_path)
    with pytest.raises(ValueError, match="phase=pilot"):
        write_pilot_json(
            Path("artifacts/pilot/bad.json"),
            {"phase": "confirmatory", "scientific_evidence": True},
            root=tmp_path,
        )
