from dataclasses import replace

from athena_aegis.calibration import (
    CalibrationSpecification,
    CalibrationState,
    ContextConditionedCalibration,
    EmpiricalQuantileCalibration,
)
from athena_aegis.context import make_execution_context
from athena_aegis.enforcement import EnforcementEngine
from athena_aegis.oos import DiagonalGaussianSupport, ExactStrataSupport, StandardizedDistanceSupport
from athena_aegis.policies import (
    Action, AssuranceInput, P0ServeAlways, P2GlobalCalibrated, P4OOSAbstention,
    P5RecoveryEnforcement,
)
from athena_aegis.recovery import CallbackRecoveryStrategy


def context(backend, error, window):
    return make_execution_context(
        local={"calibration_window_id": window},
        provider={"backend_id": backend, "gate_error_summary": {"mean": error}},
    )


def test_exact_strata_abstains_on_unseen_context():
    model = ExactStrataSupport(("backend_id",)).fit([context("a", 0.01, "w1")])
    assert model.evaluate(context("a", 0.02, "w2")).is_supported
    decision = model.evaluate(context("b", 0.01, "w2"))
    assert not decision.is_supported
    policy = P4OOSAbstention()
    outcome = policy.decide(AssuranceInput(True, CalibrationState.VALID, decision))
    assert outcome.state == "CONTEXT_OOS"
    assert outcome.action is Action.HOLD


def test_distance_and_density_baselines_are_interpretable():
    references = [context("a", 0.010, "w1"), context("a", 0.012, "w2"), context("a", 0.011, "w3")]
    near = context("a", 0.011, "t")
    far = context("a", 0.050, "t")
    distance = StandardizedDistanceSupport(("gate_error_summary",), 3.0).fit(references)
    density = DiagonalGaussianSupport(("gate_error_summary",), 0.01).fit(references)
    assert distance.evaluate(near).is_supported and not distance.evaluate(far).is_supported
    assert density.evaluate(near).is_supported and not density.evaluate(far).is_supported


def test_finite_sample_quantile_and_policies():
    specification = CalibrationSpecification("p", "request", "conditional exchangeability", "w1", "backend=a", "request", "refit on expiry", 0.2)
    model = EmpiricalQuantileCalibration(specification).fit([0.1, 0.2, 0.3, 0.4])
    assert model.accepts(0.3)
    assert not model.accepts(0.5)
    evidence = AssuranceInput(True, CalibrationState.VALID, None)
    assert P0ServeAlways().decide(evidence).action is Action.ALLOW
    assert P2GlobalCalibrated().decide(evidence).action is Action.ALLOW


def test_context_conditioned_calibration_marks_unseen_or_declares_p3_fallback():
    specification = CalibrationSpecification("p", "request", "conditional exchangeability", "w1", "backend", "request", "refit on expiry", 0.2)
    strict = ContextConditionedCalibration(specification, allow_global_fallback=False).fit({("a",): [0.1, 0.2, 0.3]})
    assert strict.evaluate(("b",), 0.1).state is CalibrationState.CONTEXT_OOS
    p3 = ContextConditionedCalibration(specification, allow_global_fallback=True).fit({("a",): [0.1, 0.2, 0.3]})
    decision = p3.evaluate(("b",), 0.1)
    assert decision.state is CalibrationState.VALID and decision.used_global_fallback


def test_p5_recovery_is_an_executed_service_consequence():
    unsupported = ExactStrataSupport(("backend_id",)).fit([context("a", 0.01, "w1")]).evaluate(context("b", 0.01, "t"))
    decision = P5RecoveryEnforcement().decide(AssuranceInput(True, CalibrationState.VALID, unsupported))
    assert decision.action is Action.RECALIBRATE
    strategy = CallbackRecoveryStrategy("recal-v1", Action.RECALIBRATE, lambda request, prior: {"verified": True})
    result = EnforcementEngine({Action.RECALIBRATE: strategy}).enforce(decision, {}, {"verified": False})
    assert result.served and result.recovery and result.recovery.success


def test_binding_failure_triggers_block_before_candidate_is_served():
    supported = ExactStrataSupport(("backend_id",)).fit([context("a", 0.01, "w1")]).evaluate(context("a", 0.01, "t"))
    decision = P5RecoveryEnforcement().decide(AssuranceInput(True, CalibrationState.VALID, supported, binding_valid=False))
    assert decision.action is Action.BLOCK
    assert not EnforcementEngine().enforce(decision, {}, "unsafe").served


def test_p5_reject_requests_rerun_then_can_fallback():
    supported = ExactStrataSupport(("backend_id",)).fit([context("a", 0.01, "w1")]).evaluate(context("a", 0.01, "t"))
    first = P5RecoveryEnforcement().decide(AssuranceInput(False, CalibrationState.VALID, supported))
    assert first.action is Action.RERUN
    second = P5RecoveryEnforcement().decide(
        AssuranceInput(False, CalibrationState.VALID, supported, rerun_available=False)
    )
    assert second.action is Action.FALLBACK
