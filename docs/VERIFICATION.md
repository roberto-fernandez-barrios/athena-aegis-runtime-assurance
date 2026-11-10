# Verification of public release 5.1.0

Local analysis environment: Windows 11, Python 3.13.12, NumPy 2.3.5, Matplotlib 3.11.0. Both ordinary and isolated (-I) invocations from another working directory passed: 7,492 unchanged artifact checks, zero discrepancies, ten software tests. All 29 generated files matched byte for byte between the two runs. These counts refer to scientific reproduction, separately from the public-manifest checks.

All 147 manifested artifact files match the sealed v5.1 export byte for byte. The original historical code, separate corrected KC-B4 code and editorial wrapper are untouched. Results remain 8/10, p=0.0546875, 5/10 retained-only, 56 retained outputs and four fallbacks; the direct comparator accepts 60/60 and separately 12/12.

Both preprints compile with MiKTeX-pdfTeX 4.27 (MiKTeX 26.5), with no unresolved references or overfull boxes. They remain 23 and 14 pages. Main page 20 and supplement pages 10–14 were visually reviewed after the DOI statement was added: no clipped text, overlap or illegible tables. All other pages are pixel-identical to v5.1 at the documented comparison resolution (72 dpi). The vector figure files and third-party template/style bytes are unchanged. The verification compares content and renderings; PDF binary identity is not required after archival metadata changes.

CITATION.cff validates against the official CFF 1.2.0 schema. Relative Markdown targets exist. A scan of public text and PDF extraction found no credential, CRN, raw provider job identifier or private user path; explicit exclusions are a public BibTeX key and two standard TeX control names matching a broad pattern. Pattern scanning is not a universal secret detector.

The final downloadable archive is checked again from a clean extraction. GitHub Actions performs independent ordinary/isolated runs on the pinned Windows and Linux analysis environments; the workflow run, rather than this document, is authoritative for its current status. Compilation logs and source/render comparison summaries are in paper_build_report.json and source_equivalence.json. The downloadable verification report records the archive SHA-256 and clean-extraction result.

These checks do not authenticate provider records or private HMACs, replay the complete acquisition state machine, attest pre-acquisition temporal precedence or establish incremental utility of reference renewal. No provider was accessed to prepare or test the publication.
