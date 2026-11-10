# Artifact and evidence map

| Scientific object | Entry point |
|---|---|
| Workload, counts, matrices and complete/incomplete units | `artifact/data/numerical/` |
| Historical policies, endpoints, protocol and amendments | `artifact/data/`, with original identities in the artifact manifests |
| Numerical reconstruction and direct comparator | `artifact/reproduce.py` |
| Original frozen analysis | `artifact/code/historical/` |
| Separate post-campaign KC-B4 correction | `artifact/code/v5_corrected/` |
| Selected acquisition/decision sources for inspection | `artifact/code/inspection_only/` (not executed) |
| Retrospective rules | `artifact/RETROSPECTIVE_SPECIFICATION.md` |
| Context comparison rules and calculation | `artifact/CONTEXT_METHOD.md`, `artifact/context_transitions.py` |
| Ten context rows and complete old/new leaf differences | `artifact/context_description/` |
| Input integrity | `artifact/INPUT_MANIFEST.json`, `artifact/MANIFEST.json` |
| Public package integrity | `PUBLIC_MANIFEST.json` |

**Do not conflate five properties:** context binding; conformity to a reference; absolute numerical correctness; physical versus fallback source; and meeting the deadline. The scientific safety analysis is not a claim that the historical service prevented all incorrect or late outputs.

The 12-transition operational path includes C05/C09 with incomplete references. The historical test uses ten usable windows, eight successes and the null 0.5. Bootstrap C01/C02 are separate attempts. Descriptive context comparisons, direct-oracle decisions and software counterexamples are revision analyses, not additional physical experiments or an earlier preregistration.
