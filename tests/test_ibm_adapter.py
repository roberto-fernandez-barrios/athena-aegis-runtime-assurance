from dataclasses import dataclass

from athena_aegis.providers import BackendSummary, CountsResult, select_pilot_backend
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


def test_sampler_v2_live_shaped_result_is_normalized():
    adapter = IBMRuntimeAdapter(service=Service(), pseudonym_key=b"p" * 32)
    handle = type("Handle", (), {"raw_job": RuntimeJob()})()
    result = adapter.result(handle)
    assert isinstance(result, CountsResult)
    assert result.get_counts() == {"0": 7, "1": 1}
    assert adapter.status(handle) == "DONE"


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
