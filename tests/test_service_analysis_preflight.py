from athena_aegis.analysis.build_endpoint_tables import build
from athena_aegis.analysis.build_metadata_matrix import PRINCIPALS, rows
from athena_aegis.calibration import CalibrationState
from athena_aegis.enforcement import EnforcementEngine
from athena_aegis.oos import SupportDecision
from athena_aegis.policies import AssuranceInput, P4OOSAbstention
from athena_aegis.providers.ibm_preflight import run_preflight
from athena_aegis.service import HSaaSOrchestrator


def test_hsaas_service_path_returns_or_withholds_result():
    orchestrator = HSaaSOrchestrator(P4OOSAbstention(), EnforcementEngine())
    supported = SupportDecision(True, 1.0, "seen", ("w1",))
    output = orchestrator.complete(
        request={"id": 1},
        candidate_result={"correct": True},
        assurance=AssuranceInput(True, CalibrationState.VALID, supported),
        correctness_oracle=lambda result: float(result["correct"]),
    )
    assert output.enforcement.served and output.service_correctness == 1.0
    unsupported = SupportDecision(False, 0.0, "unseen", ("w1",))
    held = orchestrator.complete(
        request={"id": 2}, candidate_result="bad",
        assurance=AssuranceInput(True, CalibrationState.VALID, unsupported),
    )
    assert not held.enforcement.served


def test_endpoint_builder_preserves_zero_denominators_and_units():
    records = [
        {"unsafe_eligible": True, "unsafe_continuation": True},
        {"unsafe_eligible": True, "unsafe_continuation": False},
    ]
    endpoints = {row["endpoint"]: row for row in build(records)}
    assert endpoints["unsafe_continuation_rate"]["estimate"] == 0.5
    assert endpoints["false_hold_rate"]["denominator"] == 0


def test_metadata_matrix_is_complete_cartesian_product():
    matrix = rows()
    assert len(matrix) == len(PRINCIPALS) * 16
    assert {row["principal"] for row in matrix} == set(PRINCIPALS)


def test_preflight_without_credential_is_zero_cost_and_sanitized():
    report = run_preflight(None, "none", "ibm_quantum_platform")
    assert report["credential_found"] == "no"
    assert report["authentication_test"] == "not_attempted"
    assert report["job_submitted"] is False
    assert "token" not in report
