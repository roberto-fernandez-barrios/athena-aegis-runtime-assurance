# IBM QPU connectivity smoke result

Date: 2026-09-11. Label: **CONNECTIVITY_SMOKE_TEST —
NOT_SCIENTIFIC_EVIDENCE**.

The predeclared one-qubit Hadamard/measurement circuit was submitted once to
the frozen physical backend with 32 shots and optimization level 0. The Runtime
job completed with status `DONE`; all 32 shots were normalized through the
provider-neutral `CountsResult` interface. No retry was required.

The end-to-end path passed:

`ProviderAdapter -> IBMRuntimeAdapter -> ExecutionContext -> EvidenceEnvelope
-> canonical digest/local signature -> P4 policy -> enforcement`.

ExecutionContext captured 30 of 37 fields. The seven unavailable fields were
session ID, resilience options, dynamical decoupling options, measurement
mitigation options, kernel definition, dataset/workload digest and model
reference version; their unavailable status is explicit rather than inferred.
Job-level scheduling metadata exposed timestamps, usage and usage estimation.

Local wall clock was 14.344 seconds. The provider account usage endpoint moved
from zero to two consumed seconds, leaving 5,998 of 6,000 allocated seconds.
This is observable quota usage, not monetary cost and not a benchmark.

The envelope digest and local HMAC signature verify. Raw job/session/account and
instance identifiers are absent; the retained job reference is a keyed
pseudonym. The pilot gate is therefore open. This smoke result is excluded from
all scientific analysis and from any future confirmatory dataset.

During post-pilot verification, nondeterministic QPY serialization was replaced
by the deterministic OpenQASM-2-plus-final-layout circuit projection. The smoke
context and envelope were recomputed and locally re-sealed; no count, provider
timestamp, QPU result or job execution changed, and no additional job was sent.
