# Metadata exposure matrix v1

Generated; do not edit by hand.

| principal | metadata_field | visibility | necessity | sensitivity | retention | minimization_option | origin |
|---|---|---|---|---|---|---|---|
| client | client_request_id | required/visible | request correlation | medium | campaign | HMAC pseudonym outside client boundary | direct |
| client | raw_input_or_dataset | not exposed by design | none | high | none | retain digest or approved features only | direct |
| client | dataset_workload_digest | not exposed by design | none | medium | none | domain separation and access control | derived |
| client | logical_circuit | not exposed by design | none | high | none | send only necessary circuit; no confidentiality claim | direct |
| client | circuit_semantic_hash | not exposed by design | none | medium | none | hash does not hide a small candidate space | derived |
| client | transpiled_circuit | not exposed by design | none | high | none | artifact consumer receives digest by default | direct |
| client | layout_and_qubit_subset | not exposed by design | none | medium | none | release aggregate or coded stratum | provider/local |
| client | backend_id_and_version | not exposed by design | none | low | none | retain because scientifically necessary | provider |
| client | raw_provider_job_id | not exposed by design | none | high | none | replace with keyed pseudonym before evidence storage | provider |
| client | pseudonymized_job_id | not exposed by design | none | medium | none | separate local key and rotate by campaign | derived |
| client | calibration_summaries | not exposed by design | none | medium | none | aggregate T1/T2/error; omit per-qubit detail unless needed | provider |
| client | queue_scheduling_metadata | not exposed by design | none | medium | none | aggregate timestamps/counts and report missingness | provider |
| client | raw_result | not exposed by design | none | high | none | release digest/aggregate; controlled raw access | provider |
| client | result_digests | not exposed by design | none | low | none | retain | derived |
| client | decision_and_action | required/visible | assurance/enforcement audit | medium | artifact life | omit client identifiers | local |
| client | recovery_outcome | required/visible | primary endpoint | medium | artifact life | release aggregate plus sealed de-identified record | local |
| AEGIS service | client_request_id | required/visible | request correlation | medium | campaign | HMAC pseudonym outside client boundary | direct |
| AEGIS service | raw_input_or_dataset | required/visible | workload preparation | high | minimum execution period | retain digest or approved features only | direct |
| AEGIS service | dataset_workload_digest | required/visible | reproducibility | medium | artifact life | domain separation and access control | derived |
| AEGIS service | logical_circuit | required/visible | quantum execution | high | minimum provider/service period | send only necessary circuit; no confidentiality claim | direct |
| AEGIS service | circuit_semantic_hash | required/visible | identity binding | medium | artifact life | hash does not hide a small candidate space | derived |
| AEGIS service | transpiled_circuit | required/visible | provider execution and local verification | high | minimum experiment period | artifact consumer receives digest by default | direct |
| AEGIS service | layout_and_qubit_subset | required/visible | context validity | medium | study plus audit period | release aggregate or coded stratum | provider/local |
| AEGIS service | backend_id_and_version | required/visible | context validity | low | artifact life | retain because scientifically necessary | provider |
| AEGIS service | raw_provider_job_id | required/visible | job retrieval | high | active retrieval only | replace with keyed pseudonym before evidence storage | provider |
| AEGIS service | pseudonymized_job_id | required/visible | provenance linking | medium | study plus audit period | separate local key and rotate by campaign | derived |
| AEGIS service | calibration_summaries | required/visible | support model | medium | artifact life | aggregate T1/T2/error; omit per-qubit detail unless needed | provider |
| AEGIS service | queue_scheduling_metadata | required/visible | context covariate when exposed | medium | study plus audit period | aggregate timestamps/counts and report missingness | provider |
| AEGIS service | raw_result | required/visible | postprocessing/reanalysis | high | restricted study period | release digest/aggregate; controlled raw access | provider |
| AEGIS service | result_digests | required/visible | evidence integrity | low | artifact life | retain | derived |
| AEGIS service | decision_and_action | required/visible | assurance/enforcement audit | medium | artifact life | omit client identifiers | local |
| AEGIS service | recovery_outcome | required/visible | primary endpoint | medium | artifact life | release aggregate plus sealed de-identified record | local |
| classical orchestrator | client_request_id | required/visible | request correlation | medium | campaign | HMAC pseudonym outside client boundary | direct |
| classical orchestrator | raw_input_or_dataset | required/visible | workload preparation | high | minimum execution period | retain digest or approved features only | direct |
| classical orchestrator | dataset_workload_digest | required/visible | reproducibility | medium | artifact life | domain separation and access control | derived |
| classical orchestrator | logical_circuit | required/visible | quantum execution | high | minimum provider/service period | send only necessary circuit; no confidentiality claim | direct |
| classical orchestrator | circuit_semantic_hash | required/visible | identity binding | medium | artifact life | hash does not hide a small candidate space | derived |
| classical orchestrator | transpiled_circuit | required/visible | provider execution and local verification | high | minimum experiment period | artifact consumer receives digest by default | direct |
| classical orchestrator | layout_and_qubit_subset | required/visible | context validity | medium | study plus audit period | release aggregate or coded stratum | provider/local |
| classical orchestrator | backend_id_and_version | required/visible | context validity | low | artifact life | retain because scientifically necessary | provider |
| classical orchestrator | raw_provider_job_id | not exposed by design | none | high | none | replace with keyed pseudonym before evidence storage | provider |
| classical orchestrator | pseudonymized_job_id | required/visible | provenance linking | medium | study plus audit period | separate local key and rotate by campaign | derived |
| classical orchestrator | calibration_summaries | required/visible | support model | medium | artifact life | aggregate T1/T2/error; omit per-qubit detail unless needed | provider |
| classical orchestrator | queue_scheduling_metadata | required/visible | context covariate when exposed | medium | study plus audit period | aggregate timestamps/counts and report missingness | provider |
| classical orchestrator | raw_result | required/visible | postprocessing/reanalysis | high | restricted study period | release digest/aggregate; controlled raw access | provider |
| classical orchestrator | result_digests | required/visible | evidence integrity | low | artifact life | retain | derived |
| classical orchestrator | decision_and_action | required/visible | assurance/enforcement audit | medium | artifact life | omit client identifiers | local |
| classical orchestrator | recovery_outcome | required/visible | primary endpoint | medium | artifact life | release aggregate plus sealed de-identified record | local |
| provider | client_request_id | not exposed by design | none | medium | none | HMAC pseudonym outside client boundary | direct |
| provider | raw_input_or_dataset | not exposed by design | none | high | none | retain digest or approved features only | direct |
| provider | dataset_workload_digest | not exposed by design | none | medium | none | domain separation and access control | derived |
| provider | logical_circuit | required/visible | quantum execution | high | minimum provider/service period | send only necessary circuit; no confidentiality claim | direct |
| provider | circuit_semantic_hash | not exposed by design | none | medium | none | hash does not hide a small candidate space | derived |
| provider | transpiled_circuit | required/visible | provider execution and local verification | high | minimum experiment period | artifact consumer receives digest by default | direct |
| provider | layout_and_qubit_subset | required/visible | context validity | medium | study plus audit period | release aggregate or coded stratum | provider/local |
| provider | backend_id_and_version | required/visible | context validity | low | artifact life | retain because scientifically necessary | provider |
| provider | raw_provider_job_id | required/visible | job retrieval | high | active retrieval only | replace with keyed pseudonym before evidence storage | provider |
| provider | pseudonymized_job_id | not exposed by design | none | medium | none | separate local key and rotate by campaign | derived |
| provider | calibration_summaries | not exposed by design | none | medium | none | aggregate T1/T2/error; omit per-qubit detail unless needed | provider |
| provider | queue_scheduling_metadata | required/visible | context covariate when exposed | medium | study plus audit period | aggregate timestamps/counts and report missingness | provider |
| provider | raw_result | required/visible | postprocessing/reanalysis | high | restricted study period | release digest/aggregate; controlled raw access | provider |
| provider | result_digests | not exposed by design | none | low | none | retain | derived |
| provider | decision_and_action | not exposed by design | none | medium | none | omit client identifiers | local |
| provider | recovery_outcome | not exposed by design | none | medium | none | release aggregate plus sealed de-identified record | local |
| auditor/verifier | client_request_id | required/visible | request correlation | medium | campaign | HMAC pseudonym outside client boundary | direct |
| auditor/verifier | raw_input_or_dataset | not exposed by design | none | high | none | retain digest or approved features only | direct |
| auditor/verifier | dataset_workload_digest | required/visible | reproducibility | medium | artifact life | domain separation and access control | derived |
| auditor/verifier | logical_circuit | not exposed by design | none | high | none | send only necessary circuit; no confidentiality claim | direct |
| auditor/verifier | circuit_semantic_hash | required/visible | identity binding | medium | artifact life | hash does not hide a small candidate space | derived |
| auditor/verifier | transpiled_circuit | required/visible | provider execution and local verification | high | minimum experiment period | artifact consumer receives digest by default | direct |
| auditor/verifier | layout_and_qubit_subset | required/visible | context validity | medium | study plus audit period | release aggregate or coded stratum | provider/local |
| auditor/verifier | backend_id_and_version | required/visible | context validity | low | artifact life | retain because scientifically necessary | provider |
| auditor/verifier | raw_provider_job_id | not exposed by design | none | high | none | replace with keyed pseudonym before evidence storage | provider |
| auditor/verifier | pseudonymized_job_id | required/visible | provenance linking | medium | study plus audit period | separate local key and rotate by campaign | derived |
| auditor/verifier | calibration_summaries | required/visible | support model | medium | artifact life | aggregate T1/T2/error; omit per-qubit detail unless needed | provider |
| auditor/verifier | queue_scheduling_metadata | required/visible | context covariate when exposed | medium | study plus audit period | aggregate timestamps/counts and report missingness | provider |
| auditor/verifier | raw_result | required/visible | postprocessing/reanalysis | high | restricted study period | release digest/aggregate; controlled raw access | provider |
| auditor/verifier | result_digests | required/visible | evidence integrity | low | artifact life | retain | derived |
| auditor/verifier | decision_and_action | required/visible | assurance/enforcement audit | medium | artifact life | omit client identifiers | local |
| auditor/verifier | recovery_outcome | required/visible | primary endpoint | medium | artifact life | release aggregate plus sealed de-identified record | local |
| artifact consumer | client_request_id | not exposed by design | none | medium | none | HMAC pseudonym outside client boundary | direct |
| artifact consumer | raw_input_or_dataset | not exposed by design | none | high | none | retain digest or approved features only | direct |
| artifact consumer | dataset_workload_digest | required/visible | reproducibility | medium | artifact life | domain separation and access control | derived |
| artifact consumer | logical_circuit | not exposed by design | none | high | none | send only necessary circuit; no confidentiality claim | direct |
| artifact consumer | circuit_semantic_hash | required/visible | identity binding | medium | artifact life | hash does not hide a small candidate space | derived |
| artifact consumer | transpiled_circuit | not exposed by design | none | high | none | artifact consumer receives digest by default | direct |
| artifact consumer | layout_and_qubit_subset | not exposed by design | none | medium | none | release aggregate or coded stratum | provider/local |
| artifact consumer | backend_id_and_version | required/visible | context validity | low | artifact life | retain because scientifically necessary | provider |
| artifact consumer | raw_provider_job_id | not exposed by design | none | high | none | replace with keyed pseudonym before evidence storage | provider |
| artifact consumer | pseudonymized_job_id | not exposed by design | none | medium | none | separate local key and rotate by campaign | derived |
| artifact consumer | calibration_summaries | required/visible | support model | medium | artifact life | aggregate T1/T2/error; omit per-qubit detail unless needed | provider |
| artifact consumer | queue_scheduling_metadata | not exposed by design | none | medium | none | aggregate timestamps/counts and report missingness | provider |
| artifact consumer | raw_result | not exposed by design | none | high | none | release digest/aggregate; controlled raw access | provider |
| artifact consumer | result_digests | required/visible | evidence integrity | low | artifact life | retain | derived |
| artifact consumer | decision_and_action | required/visible | assurance/enforcement audit | medium | artifact life | omit client identifiers | local |
| artifact consumer | recovery_outcome | required/visible | primary endpoint | medium | artifact life | release aggregate plus sealed de-identified record | local |
