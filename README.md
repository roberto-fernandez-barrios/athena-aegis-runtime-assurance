# Operational limits of reference renewal for retained quantum-service results

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24108573.svg)](https://doi.org/10.5281/zenodo.24108573)
[![Offline reproduction](https://github.com/roberto-fernandez-barrios/athena-aegis-runtime-assurance/actions/workflows/reproduce.yml/badge.svg)](https://github.com/roberto-fernandez-barrios/athena-aegis-runtime-assurance/actions/workflows/reproduce.yml)
[![Python 3.13](https://img.shields.io/badge/Python-3.13.12-blue)](REPRODUCIBILITY.md)
[![Code: Apache-2.0](https://img.shields.io/badge/code-Apache--2.0-blue)](LICENSE)
[![Data: CC BY 4.0](https://img.shields.io/badge/data-CC_BY_4.0-lightgrey)](LICENSE-DATA)

Reproducible physical implementation study of a procedure that reconsiders retained quantum-service results after an observed context change. The study documents reference renewal, execution-context binding, incomplete references and deadline outcomes, with a retrospective direct-oracle comparison.

**Status:** author preprint prepared for *Quantum Information Processing*, collection *Quantum Software Engineering*. No journal submission or acceptance is claimed. **Public version:** `5.1.0` (paper/ESM v5.1). **Scientific scope:** implementation and operational limits; the evidence does not demonstrate incremental numerical-correctness utility of renewal over direct oracle checking.

[Read the paper](paper/manuscript.pdf) · [Supplement](paper/ESM_1.pdf) · [Reproduce](REPRODUCIBILITY.md) · [Archived release](https://doi.org/10.5281/zenodo.24108573) · [Citation](CITATION.cff) · [Data and method map](docs/ARTIFACT_MAP.md)

## Results at a glance

**12 transitions with retained results → 10 complete renewals and usable windows → 8 endpoint successes.** Five of the ten usable windows succeeded using retained physical results alone. The two bootstrap attempts are separate from these twelve transitions.

| Result | Value and interpretation |
|---|---|
| Historical endpoint | 8/10; exact one-sided p = 0.0546875; H1-B not established |
| Success using retained results alone | 5/10 usable windows |
| P5 primary output source | 56 retained physical results; 4 classical fallbacks |
| Failed usable-window endpoints | Two deadline failures |
| Direct binding-plus-oracle comparator | 60/60 usable-window physical results accepted; separately 12/12 in incomplete C05/C09 |
| Calibration in usable transitions | 390 jobs, following the fixed 39-unit reference rule |
| Reproduction inputs | 575 units with preserved count histograms; 429 scores across 11 complete references, including bootstrap |

The comparator's acceptances are retrospective decisions on the same physical evidence. Alternative deployed latency, scheduler performance, monetary cost and energy use were not measured. No P2 rejection was rescued as a retained physical result by P5. The result that a 39-unit rule requires 39 calibration units is a property of the rule; observed waiting, incomplete references, binding failures and deadline consequences are empirical findings.

## Reproduce offline

Use Python **3.13.12** and the locked analysis dependencies. No Qiskit installation, provider account, token, repository installation or QPU access is needed.

```bash
git clone https://github.com/roberto-fernandez-barrios/athena-aegis-runtime-assurance.git
cd athena-aegis-runtime-assurance
git checkout paper25-qip-v5.1.0
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
python scripts/verify_publication.py --output reproduced
```

The verifier checks the public manifest, runs the artifact from a different working directory both ordinarily and with `python -I`, and compares the results. The underlying command reports **7,492 checks, zero discrepancies and ten software tests** in the validated v5.1 environment. The wrapper checks publication integrity separately; it does not inflate the scientific check count. See [environment and verification limits](REPRODUCIBILITY.md).

```text
python /absolute/path/artifact/reproduce.py --output /absolute/output_ordinary
python -I /absolute/path/artifact/reproduce.py --output /absolute/output_isolated
```

## What can be reconstructed?

The numerical path is: preserved normalized counts → physical kernel matrices → exact classical reference and errors → reference scores and ranks → output-source decisions → window endpoints → exact binomial test and intervals. Tables, vector figures and the ten-transition context description are regenerated. Missing measurements remain missing.

The export preserves three distinct software layers: [historical analysis](artifact/code/historical/), the [post-campaign KC-B4 correction](artifact/code/v5_corrected/), and the [editorial reproduction wrapper](artifact/reproduce.py). Selected acquisition/decision sources are inspection-only snapshots. The wrapper does not replay the full acquisition runner or support guard.

## Scope and limitations

The exact oracle is available and also supplies the calibration score. Relative conformity does not guarantee absolute correctness. Usable windows were selected from temporally concentrated observations; independence and homogeneity are not established. The deadline is an evaluated outcome, not a demonstrated historical gate that prevents every late service. Reproduction relies on inherited clocks and operational flags. Hashes establish byte integrity, not private HMAC authentication, provider authenticity or independent pre-acquisition protocol timing.

Observed metadata changes define transitions under the contract. They neither establish material distribution drift nor identify its causal effect; repeated JSON views are not independent physical changes. No quantum advantage, externally required renewal, universal assurance guarantee or measured deployment savings are claimed. The manuscript remains a bounded study and may face editorial concerns about relevance or limited contribution.

## Repository map

| Path | Contents |
|---|---|
| [`artifact/`](artifact/) | Unchanged, self-contained v5.1 numerical artifact, sanitized evidence and frozen code |
| [`paper/`](paper/) | Author-preprint PDFs, complete editable sources and vector figures |
| [`docs/`](docs/) | Method, provenance, release identity, licensing and verification explanations |
| [`scripts/`](scripts/) | Offline public-package verification and paper compilation |
| [`.zenodo.json`](.zenodo.json) / [`CITATION.cff`](CITATION.cff) | Archival and citation metadata |

The public tree is curated from the verified v5.1 delivery. Existing public Git history is preserved. The older prototype remains accessible at [its historical commit](https://github.com/roberto-fernandez-barrios/athena-aegis-runtime-assurance/tree/9f1aa086f3d5ab834f7f1e56c719b3d4688d5cb8); it is not the current reproduction entry point. Private acquisition state, internal editorial reviews, correspondence, credentials and previous submission bundles are not part of this public package. Historical commit identifiers inside exported protocol documents refer to the retained local research history; those commits are not required to run this package.

## Citation and release identity

Use version DOI **[10.5281/zenodo.24108573](https://doi.org/10.5281/zenodo.24108573)** to identify this exact package and tag **[paper25-qip-v5.1.0](https://github.com/roberto-fernandez-barrios/athena-aegis-runtime-assurance/releases/tag/paper25-qip-v5.1.0)** for the source. Concept DOI **[10.5281/zenodo.24108572](https://doi.org/10.5281/zenodo.24108572)** identifies the version family. These DOIs identify the artifact, not a published journal article. The later archive does not establish preregistration precedence.

```bibtex
@software{fernandez_barrios_2026_paper25,
  author = {Fernández-Barrios, Roberto and Pastor-López, Iker and
            Pikatza-Huerga, Amaia and García Bringas, Pablo},
  title = {Operational limits of reference renewal for retained quantum-service results: reproducibility artifact},
  year = {2026},
  version = {5.1.0},
  publisher = {Zenodo},
  doi = {10.5281/zenodo.24108573}
}
```

## Authors, funding and reuse

Roberto Fernández-Barrios, Iker Pastor-López, Amaia Pikatza-Huerga and Pablo García Bringas — Faculty of Engineering, University of Deusto. Correspondence: roberto.fernandez.b@deusto.es. Author order, contributions and declarations are retained in the paper.

This work is part of grant **PID2024-155693NB-C43, ATHENA-AEGIS**, funded by **MICIU/AEI/10.13039/501100011033 and ERDF/EU**. It is a component study, not validation of the complete project. OpenAI Codex and Anthropic Claude Code assisted with drafting and language review, literature checking, analysis-code and figure preparation, and internal editorial review. The human authors retain full responsibility for the manuscript.

Code is Apache-2.0; derived evidence and documentation are CC BY 4.0. Manuscript and supplement are author preprints excluded from those licenses. Third-party template terms are retained. See [LICENSING.md](LICENSING.md), [contribution guidance](CONTRIBUTING.md) and [private security reporting](SECURITY.md).
