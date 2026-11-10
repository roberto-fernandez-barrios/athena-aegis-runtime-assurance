# Paper 2.5 — v5.1 numerical artifact

Tested analysis environment: Python 3.13.12, NumPy 2.3.5 and Matplotlib 3.11.0. Compatibility with other versions is not asserted for this closure. From a directory other than the extracted artifact, both commands were checked (replace the example absolute paths):

```text
python /absolute/extracted/artifact/reproduce.py --output /absolute/output_ordinary
python -I /absolute/extracted/artifact/reproduce.py --output /absolute/output_isolated
```

On Windows, quote absolute paths that contain spaces. `python reproduce.py` from the extracted artifact also uses these explicit packaged paths. No manual PYTHONPATH, Qiskit, credentials, installed repository or provider access is required. Editorial helpers are loaded with importlib from paths relative to the script. Outputs include `REPORT.md`, `reproduction_report.json`, reconstructed CSVs, ten unchanged software tests, vector figures and TeX tables. A nonzero exit reports input corruption or numerical discrepancies.

The input manifest identifies all distributed files; outputs are separate. `data/numerical/` is a documented whitelist export of original local records. It contains 575 bound units with six normalized 128-shot count histograms each, their matrices, all 429 scores in eleven complete references (including bootstrap), 52 additional bound calibrators from C05/C09, 72 held probes, 22 verification probes, clocks and binding-comparison fields. Counts do not survive in the original unit records for seven unbound calibrators; submission-failed, cancelled and not-submitted units also lack numerical results. All 613 attempt records remain visible. Missing counts are not reconstructed from scores.

`reproduce.py` independently implements the two-qubit ZZ statevector, histogram-to-kernel reconstruction, errors, conformal ranks, direct comparator and binomial sums/root inversion. It checks against stored quantities, reconstructs endpoints, invokes the byte-preserved historical analyzer on exported records and tests the separately corrected analyzer. `code/historical/` is byte-identical original source; `code/v5_corrected/` is the post-campaign KC-B4 change. `code/inspection_only/` preserves selected original acquisition/decision sources as text, never imported. `RETROSPECTIVE_SPECIFICATION.md` records the revision analysis rules. Synthetic software cases are not physical observations.

The exact classical matrix is regenerated from the unchanged workload definition during revision and independently checked by the distributed implementation. It is not claimed to be an original stored matrix file. The historical acquisition snapshots identify Python 3.11.0, Qiskit 2.5.2, Qiskit IBM Runtime 0.49.0, NumPy 2.4.6 and backend ibm_basquecountry version 1.0.11, 156-qubit configuration with physical support [0,1]. Those historical values are distinct from the reconstruction environment.

The direct comparator uses the same physical matrix, checks available context binding and absolute oracle thresholds (relative 0.15, maximum absolute 0.20, tolerance 1e-12), and never silently substitutes a classical output. Its acceptances are retrospective decisions, not measured deployment latency. No new reference is structurally needed for those decisions. This does not quantify money, energy or scheduling savings.

Reproduction levels must remain distinct:

* Numerical: normalized counts to matrices, reconstructed exact reference, scores, ranks, source decisions, endpoints, original binomial test and intervals.
* Integrity: hashes validate supplied bytes and identify filtered source files.
* Binding: J1 timestamp order and J2/J3 digest comparisons are rechecked; original recorded J4/integrity and binding-authentication verdicts are trust premises. Underlying provider truth and authentication are not independently established.
* HMAC: not reverified; private keys/signatures and raw provider identities are excluded.
* Provider reconciliation: historical findings only; no current provider call.
* Temporal precedence: sealing/HOLD/reference clocks are checked locally; no independent pre-acquisition protocol timestamp anchor is established.

Ancillary `data/retrospective/` records and Campaign A summaries retain the scope documented in the supplement. They are inherited summaries, not a fresh full Campaign A numerical reconstruction. B's central 60-probe decisions and ten-window contrast are recomputed from counts. Local declarations of binding do not become processor attestation through export.

This artifact contains no executable acquisition runner, keys or provider credentials. Do not modify the inputs to obtain expected results. The complete manuscript delivery and its internal editorial records are separate from this electronic supplement.

Endpoint reconstruction is conditional on the recorded usable-window set, all clocks, held_physical_result_exists, trusted_invariants_held and service_probe_qpu_rerun. The P5 rebuild does not re-execute the full stratum-support guard or the acquisition state machine. Known failed comparator predicates take precedence as REJECT; missing required inputs otherwise yield UNKNOWN.

## Supplement identification

Article: Operational limits of reference renewal for retained quantum-service results. Journal: Quantum Information Processing. Authors: Roberto Fernández-Barrios, Iker Pastor-López, Amaia Pikatza-Huerga, Pablo García Bringas. Corresponding author: Roberto Fernández-Barrios, Faculty of Engineering, University of Deusto, Avda. de las Universidades 24, 48007 Bilbao, Spain; roberto.fernandez.b@deusto.es.


## Descriptive context comparison (v5.1)

`context_transitions.py` compares each usable window with its recorded selected stale reference. `CONTEXT_METHOD.md` defines leaf matching and interpretation. `context_description/` includes the generated ten-row table, complete old/new leaf values and source hashes. The reproduction command regenerates these as `context_transitions.csv`, `context_changed_leaves.csv`, `context_transitions.json` and `tables/context_transitions.tex`. These are retrospective descriptions, not new tests, transition definitions or physical drift estimates. Counts include repeated views of parameters; named-collection order does not create differences. The historical data, historical code and separate v5 KC-B4 correction are unchanged.
