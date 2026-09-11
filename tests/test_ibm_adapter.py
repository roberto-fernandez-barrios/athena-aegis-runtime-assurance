from dataclasses import dataclass

from athena_aegis.providers.ibm_runtime import IBMRuntimeAdapter


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
