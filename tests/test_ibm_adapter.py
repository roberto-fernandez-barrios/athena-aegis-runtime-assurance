from dataclasses import dataclass
from datetime import datetime, timezone

from athena_aegis.providers import BackendSummary, CountsResult, select_pilot_backend
from athena_aegis.providers.base import transpiled_circuit_digest
from athena_aegis.providers.ibm_runtime import IBMRuntimeAdapter, _normalize_coupling_edges


@dataclass
class Status:
    operational: bool = True
    pending_jobs: int = 3
    status_msg: str = "active"


@dataclass
class Config:
    backend_name: str = "fake_backend"
    backend_version: str = "1.2.3"
    simulator: bool = False


class Coupling:
    def get_edges(self):
        return [(0, 1)]


class EdgeList:
    def __iter__(self):
        return iter(((1, 2), (0, 1)))


class Backend:
    name = "fake_backend"
    num_qubits = 2
    coupling_map = Coupling()
    target = type("Target", (), {"operation_names": ["x", "cx"]})()

    def status(self): return Status()
    def configuration(self): return Config()
    def properties(self, refresh=False): return None


class Service:
    def backends(self, instance=None): return [Backend()]
    def backend(self, name, instance=None): return Backend()


class Gate:
    gate = "cz"
    qubits = [0, 1]


class Properties:
    last_update_date = datetime(2026, 9, 11, 10, 0, tzinfo=timezone.utc)
    gates = [Gate()]

    def t1(self, qubit): return 0.0001 + qubit * 0.00001
    def t2(self, qubit): return 0.0002 + qubit * 0.00001
    def readout_error(self, qubit): return 0.01 + qubit * 0.001
    def gate_error(self, gate, qubits): return 0.002


class LiveShapedBackend(Backend):
    coupling_map = EdgeList()

    def properties(self, refresh=False): return Properties()


class LiveShapedService(Service):
    def backends(self, instance=None): return [LiveShapedBackend()]
    def backend(self, name, instance=None): return LiveShapedBackend()


def test_ibm_provider_reported_context_uses_no_network():
    adapter = IBMRuntimeAdapter(service=Service(), pseudonym_key=b"p" * 32)
    summaries = adapter.list_backends()
    assert summaries[0].pending_jobs == 3
    context = adapter.get_backend_context("fake_backend")
    assert context.value("backend_id") == "fake_backend"
    assert context.fields["backend_id"].trust.value == "untrusted"
    assert context.fields["backend_calibration_timestamp"].origin.value == "unavailable"


def test_qiskit_252_edge_list_has_canonical_projection():
    assert _normalize_coupling_edges(EdgeList()) == [[0, 1], [1, 2]]


def test_execution_context_from_live_shaped_backend_payload():
    adapter = IBMRuntimeAdapter(service=LiveShapedService(), pseudonym_key=b"p" * 32)
    context = adapter.get_backend_context("fake_backend")
    assert context.value("backend_calibration_timestamp") == "2026-09-11T10:00:00+00:00"
    assert context.value("t1_summary")["count"] == 2
    assert context.value("gate_error_summary")["mean"] == 0.002
    assert context.value("coupling_target_digest")
    assert context.fields["gate_error_summary"].origin.value == "provider_reported"


class BitArray:
    def get_counts(self):
        return {"0": 7, "1": 1}


class DataBin:
    meas = BitArray()

    def keys(self):
        return ("meas",)


class PubResult:
    data = DataBin()


class RuntimeResult:
    def __iter__(self):
        return iter((PubResult(),))


class RuntimeJob:
    def result(self):
        return RuntimeResult()

    def status(self):
        return type("Status", (), {"name": "DONE"})()


class FailedRuntimeJob:
    def result(self):
        raise RuntimeError("provider failure")


def test_sampler_v2_live_shaped_result_is_normalized():
    adapter = IBMRuntimeAdapter(service=Service(), pseudonym_key=b"p" * 32)
    handle = type("Handle", (), {"raw_job": RuntimeJob()})()
    result = adapter.result(handle)
    assert isinstance(result, CountsResult)
    assert result.get_counts() == {"0": 7, "1": 1}
    assert adapter.status(handle) == "DONE"


def test_runtime_job_failure_is_not_silently_normalized():
    adapter = IBMRuntimeAdapter(service=Service(), pseudonym_key=b"p" * 32)
    handle = type("Handle", (), {"raw_job": FailedRuntimeJob()})()
    try:
        adapter.result(handle)
    except RuntimeError as exc:
        assert str(exc) == "provider failure"
    else:
        raise AssertionError("job failure must propagate to the sanitized live runner")


def test_backend_selection_rule_is_pre_result_and_deterministic():
    candidates = [
        BackendSummary("IBM", "busy", True, 8, 127, False),
        BackendSummary("IBM", "best-z", True, 2, 127, False),
        BackendSummary("IBM", "best-a", True, 2, 5, False),
        BackendSummary("IBM", "sim", True, 0, 32, True),
        BackendSummary("IBM", "offline", False, 0, 127, False),
    ]
    selection = select_pilot_backend(candidates, required_qubits=2)
    assert selection.selected.backend_id == "best-a"
    assert [item.backend_id for item in selection.eligible] == ["best-a", "best-z", "busy"]


def test_backend_selection_rejects_insufficient_or_unavailable_candidates():
    candidates = [BackendSummary("IBM", "small", True, None, 1, False)]
    try:
        select_pilot_backend(candidates, required_qubits=2)
    except RuntimeError as exc:
        assert "no operational physical backend" in str(exc)
    else:
        raise AssertionError("selection should fail without an eligible backend")


def test_transpiled_digest_ignores_nondeterministic_circuit_object_identity():
    from qiskit import QuantumCircuit

    first = QuantumCircuit(1, 1, name="first-object")
    first.h(0)
    first.measure(0, 0)
    second = QuantumCircuit(1, 1, name="second-object")
    second.h(0)
    second.measure(0, 0)
    changed = second.copy()
    changed.x(0)
    assert transpiled_circuit_digest((first,)) == transpiled_circuit_digest((second,))
    assert transpiled_circuit_digest((first,)) != transpiled_circuit_digest((changed,))
