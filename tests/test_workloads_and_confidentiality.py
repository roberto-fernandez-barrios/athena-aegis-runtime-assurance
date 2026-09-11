import importlib.util

import pytest

from athena_aegis.confidentiality import MetadataMinimizer
from athena_aegis.workloads.fms import FMSRoutingInstance, FMSRoutingWorkload, RouteSolution


def test_fms_exact_oracle_and_quality_score():
    instance = FMSRoutingInstance("square", ((0, 0), (1, 0), (1, 1), (0, 1)))
    workload = FMSRoutingWorkload()
    prepared = workload.prepare(instance)
    oracle = prepared.classical_reference
    assert oracle.valid and oracle.route[0] == oracle.route[-1] == 0
    assert workload.correctness(oracle, prepared) == 1.0
    degraded = RouteSolution((0, 1, 3, 2, 0), 0.0, True)
    assert 0 < workload.correctness(degraded, prepared) < 1
    forged_invalid = RouteSolution((0, 1, 1, 2, 0), 0.0, True)
    assert workload.correctness(forged_invalid, prepared) == 0.0
    assert prepared.semantic_identity["scope"] == "AEGIS slice of the FMS demonstrator"


def test_metadata_minimization_is_measurable():
    source = {"raw_id": "sensitive-long-id", "backend": "ibm_test", "extra": "omit"}
    minimizer = MetadataMinimizer(frozenset({"raw_id", "backend"}), frozenset({"raw_id"}))
    result = minimizer.minimize(source)
    assert result["raw_id"].startswith("sha256:")
    assert "extra" not in result
    assert minimizer.byte_reduction(source, result) < 1.0


@pytest.mark.skipif(importlib.util.find_spec("qiskit_aer") is None, reason="quantum extra unavailable")
def test_kernel_workload_on_simulator():
    from athena_aegis.providers import SubmissionRequest
    from athena_aegis.providers.simulator import SimulatorAdapter
    from athena_aegis.workloads.kernel import KernelInstance, QuantumKernelRegressionWorkload

    workload = QuantumKernelRegressionWorkload()
    prepared = workload.prepare(KernelInstance(((0.1, 0.2), (0.3, 0.4))))
    adapter = SimulatorAdapter(seed_simulator=7)
    handle = adapter.submit(SubmissionRequest(prepared.circuits, shots=512, transpiler_seed=7))
    matrix = workload.postprocess(adapter.result(handle), prepared)
    assert matrix.shape == (2, 2)
    assert 0 <= workload.correctness(matrix, prepared) <= 1
    assert adapter.capture_execution_evidence(handle, SubmissionRequest(prepared.circuits, 512, transpiler_seed=7)).value("job_id").startswith("hmac-sha256:")
