# ATHENA-AEGIS Runtime Assurance (Paper 2.5)

Independent research codebase for **context-conditioned longitudinal
assurance of hybrid quantum-classical services under non-stationary QPU
execution**.

This is not a continuation release of Paper 1.5. Paper 1.5 remains frozen in
`roberto-fernandez-barrios/hybrid-quantum-classical-integrity` at
`paper15-q1-v1.3.8`. Its local/offline calibrated policy is an explicit
baseline here; its science, releases, and tags are not modified.

## Scientific boundary

The system binds execution context to calibration validity, abstains when the
context is outside calibration support, enforces a declared response, and
measures the resulting service consequence. Provider metadata is called
**provider-reported execution evidence**. A local signature authenticates only
the locally captured envelope from capture onward; it is not provider
attestation.

The confirmatory QPU campaign is not authorized by this repository state.
The non-confirmatory QPU pilot is complete; its result and design candidates are
in `docs/QPU_PILOT_RESULT.md`. `manuscript/PREREGISTRATION_v1.md` remains
`DRAFT, NOT FROZEN` until the author reviews that result and explicitly approves
the confirmatory window/cadence/job budget.

## Implemented now

- versioned `ExecutionContext` with field-level origin and trust labels;
- versioned `EvidenceEnvelope`, canonical JSON, SHA-256, provenance links,
  and optional local signing;
- authenticated item/prediction/evaluation-label binding;
- isolated IBM Runtime and simulator provider adapters;
- Paper-1.5-compatible compute-uncompute kernel regression workload;
- AEGIS slice of the FMS demonstrator with an exact classical routing oracle
  and a QAOA/QUBO hand-off skeleton;
- exact-strata, standardized-distance, and diagonal-density context-support
  baselines;
- explicit calibration assumptions and finite-sample empirical quantiles;
- P0-P5 assurance policies, enforcement records, and recovery strategies;
- metadata minimization and a generated principal-by-field exposure matrix;
- machine-readable intervention, metric, and experiment registries.

## Local verification

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.venv\Scripts\python.exe -m pip install -e . --no-deps
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m athena_aegis.analysis.build_metadata_matrix
.venv\Scripts\python.exe -m athena_aegis.analysis.build_manifest
.venv\Scripts\python.exe scripts\secret_scan.py
```

IBM access is optional for development. Credentials are never accepted as
command-line arguments and never written by the preflight utility. Load a
credential into the current process or use a Qiskit saved account, then run:

```powershell
.venv\Scripts\athena-aegis-preflight.exe --output artifacts/preflight/ibm_preflight.json
```

The command is read-only: authentication, instance/backend enumeration,
status, target/configuration, calibration summaries, queue metadata when
exposed, and account usage when exposed. It submits no job.

## Scope limits

No current artifact in this repository is physical-QPU scientific evidence.
The connectivity smoke and four pilot jobs are physical-QPU infrastructure and
feasibility records with `scientific_evidence=false`.
The FMS implementation is the **AEGIS slice of the FMS demonstrator**, not the
global consortium demonstrator. Multi-tenancy, provider-internal scheduling,
cryptographic provider attestation, and circuit confidentiality are not
claimed.
