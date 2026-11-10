# Reproduction guide

## Environment

The v5.1 analysis environment actually tested locally is Python 3.13.12, NumPy 2.3.5 and Matplotlib 3.11.0 on Windows. `requirements-lock.txt` pins these and their installed plotting dependencies. The CI workflow checks the same Python/dependency versions on Windows and Linux; a green run demonstrates only its recorded environment. No other Python release is promised.

Create a virtual environment, activate it and run `python -m pip install -r requirements-lock.txt`. These dependencies are only for offline analysis and plotting. Package installation requires internet access; reconstruction itself does not. Historical acquisition versions remain distinct: Python 3.11.0, Qiskit 2.5.2, Qiskit IBM Runtime 0.49.0, NumPy 2.4.6. They are documented provenance, not required installations.

## One-command check

```text
python scripts/verify_publication.py --output reproduced
```

This validates the complete public manifest and nested artifact manifest, runs numerical reconstruction twice from a temporary working directory with PYTHONPATH removed (ordinary and isolated `-I`), and compares all generated outputs byte for byte within that environment. `publication_verification.json` records package integrity separately from the 7,492 numerical checks and ten software tests. Output must be outside the input tree; an existing output directory is refused.

For the standalone ESM_2.zip, extract it first, then use absolute paths from any other directory:

```text
python /absolute/extracted/reproduce.py --output /absolute/output_ordinary
python -I /absolute/extracted/reproduce.py --output /absolute/output_isolated
```

On Windows, quote paths containing spaces and replace example paths with real ones. No PYTHONPATH, installed repository, credentials or provider service is needed. The wrapper does not import an acquisition adapter. `REPORT.md` explains reconstructed quantities, comparisons and limits; JSON and CSV outputs support machine inspection. Do not modify tolerances, thresholds or data to produce expected results.

## Preserved checks and equivalence

The source artifact's comparison rules and numerical tolerances are unchanged. The exact test is recomputed from reconstructed successes, not read as a stored p-value. Ten software tests include historical versus separately corrected KC-B4 behavior and the synthetic conformity/absolute-correctness counterexample. Context descriptions are recomputed from sanitized projections against the stale reference actually selected.

Binary identity is required for distributed inputs and preserved code. Floating-point checks use the original artifact rules, including the documented 1e-12 tolerance where applicable. We do not require cross-platform PDF binary identity: font/rasterizer and compilation metadata can differ. Ordinary and isolated runs are compared within the same environment. A new numerical discrepancy is a failure, not a reason to relax a tolerance.

## Rebuild the paper

With a complete local LaTeX installation (pdflatex and BibTeX), run:

```text
python scripts/build_paper.py --output /absolute/new/build_directory
```

The build uses supplied standalone sources, Springer class, bibliography style and vector figures; it disables shell escape and does not install missing TeX packages. The returned report records logs, source/PDF hashes and warnings. These layout tools are separate from the locked numerical environment. A SOURCE_DATE_EPOCH convention stabilizes compilation metadata; it is not a historical timestamp attestation.

## Limits

Reproduction reaches preserved count histograms, not a new QPU execution. The exact reference is independently regenerated from the workload, not mislabeled as an original measured file. Missing counts for unbound units stay absent. Operational states, the usable-window set and some binding verdicts are recorded premises. No private HMAC, provider reconciliation, independent pre-acquisition timestamp or full acquisition/support-guard replay is available. See `artifact/README.md` and the supplement for the precise boundary.
