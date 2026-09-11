# Confidentiality and metadata exposure

The generated matrix crosses the required principals—client, AEGIS service,
classical orchestrator, provider, auditor/verifier, and artifact consumer—with
each operational metadata field's visibility, necessity, sensitivity,
retention, and minimization option. Source rules live in
`src/athena_aegis/analysis/build_metadata_matrix.py`; generated CSV/Markdown
artifacts are reproducible outputs.

## Measurable controls

- replace raw provider job/session IDs with campaign-keyed HMAC pseudonyms;
- expose result, input, and transpiled artifacts as digests/aggregates unless
  raw access is scientifically necessary;
- summarize per-qubit T1/T2/readout/gate metrics when individual detail adds no
  support-model value;
- record queue/scheduling fields only when provider-visible and report
  missingness;
- measure serialized bytes before/after minimization, retained field count,
  false joins, and audit verification success.

The authenticated envelope protects integrity after local capture. Hashing does
not provide confidentiality for low-entropy values. Pseudonymization is not
anonymization. The provider necessarily sees submitted circuits and execution
material under its service model. This study makes no claim that IBM guarantees
circuit/data confidentiality and no claim about unobservable provider-internal
metadata. If exposure/minimization endpoints cannot be measured, KC5 moves this
analysis to a project technical report.
