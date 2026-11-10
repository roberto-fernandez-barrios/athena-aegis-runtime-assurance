# Author preprints and editable sources

`manuscript.pdf` and `ESM_1.pdf` correspond to the standalone sources under `source/`. They are author preprints prepared for QIP, not accepted articles. The only change from the sealed v5.1 delivery is the DOI/archive-availability wording recorded in `availability_update.diff`. Scientific content, authorship and declarations are unchanged.

Run `python scripts/build_paper.py --output /absolute/new/build_directory` from the repository root with a complete local LaTeX installation. Numerical inputs/outputs and fonts/graphics are documented separately. The four vector figure PDFs retain their original bytes. Springer class and bibliography-style files retain their original bytes and notices.

No cover letter, internal model review or submission form data are included in this public directory. Manuscript licensing differs from code and data; see `../LICENSING.md`.
