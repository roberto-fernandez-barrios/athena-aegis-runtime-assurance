"""Build the principal-by-metadata exposure matrix from declared rules."""

from __future__ import annotations

import csv
from pathlib import Path


PRINCIPALS = (
    "client", "AEGIS service", "classical orchestrator", "provider",
    "auditor/verifier", "artifact consumer",
)

FIELDS = {
    "client_request_id": ("direct", "request correlation", "medium", "campaign", "HMAC pseudonym outside client boundary"),
    "raw_input_or_dataset": ("direct", "workload preparation", "high", "minimum execution period", "retain digest or approved features only"),
    "dataset_workload_digest": ("derived", "reproducibility", "medium", "artifact life", "domain separation and access control"),
    "logical_circuit": ("direct", "quantum execution", "high", "minimum provider/service period", "send only necessary circuit; no confidentiality claim"),
    "circuit_semantic_hash": ("derived", "identity binding", "medium", "artifact life", "hash does not hide a small candidate space"),
    "transpiled_circuit": ("direct", "provider execution and local verification", "high", "minimum experiment period", "artifact consumer receives digest by default"),
    "layout_and_qubit_subset": ("provider/local", "context validity", "medium", "study plus audit period", "release aggregate or coded stratum"),
    "backend_id_and_version": ("provider", "context validity", "low", "artifact life", "retain because scientifically necessary"),
    "raw_provider_job_id": ("provider", "job retrieval", "high", "active retrieval only", "replace with keyed pseudonym before evidence storage"),
    "pseudonymized_job_id": ("derived", "provenance linking", "medium", "study plus audit period", "separate local key and rotate by campaign"),
    "calibration_summaries": ("provider", "support model", "medium", "artifact life", "aggregate T1/T2/error; omit per-qubit detail unless needed"),
    "queue_scheduling_metadata": ("provider", "context covariate when exposed", "medium", "study plus audit period", "aggregate timestamps/counts and report missingness"),
    "raw_result": ("provider", "postprocessing/reanalysis", "high", "restricted study period", "release digest/aggregate; controlled raw access"),
    "result_digests": ("derived", "evidence integrity", "low", "artifact life", "retain"),
    "decision_and_action": ("local", "assurance/enforcement audit", "medium", "artifact life", "omit client identifiers"),
    "recovery_outcome": ("local", "primary endpoint", "medium", "artifact life", "release aggregate plus sealed de-identified record"),
}


VISIBLE = {
    "client": {"client_request_id", "decision_and_action", "recovery_outcome"},
    "AEGIS service": set(FIELDS),
    "classical orchestrator": set(FIELDS) - {"raw_provider_job_id"},
    "provider": {"logical_circuit", "transpiled_circuit", "layout_and_qubit_subset", "backend_id_and_version", "raw_provider_job_id", "queue_scheduling_metadata", "raw_result"},
    "auditor/verifier": set(FIELDS) - {"raw_input_or_dataset", "raw_provider_job_id", "logical_circuit"},
    "artifact consumer": {"dataset_workload_digest", "circuit_semantic_hash", "backend_id_and_version", "calibration_summaries", "result_digests", "decision_and_action", "recovery_outcome"},
}


def rows() -> list[dict[str, str]]:
    result = []
    for principal in PRINCIPALS:
        for field, (origin, necessity, sensitivity, retention, minimization) in FIELDS.items():
            visible = field in VISIBLE[principal]
            result.append({
                "principal": principal,
                "metadata_field": field,
                "visibility": "required/visible" if visible else "not exposed by design",
                "necessity": necessity if visible else "none",
                "sensitivity": sensitivity,
                "retention": retention if visible else "none",
                "minimization_option": minimization,
                "origin": origin,
            })
    return result


def main() -> None:
    output_dir = Path("artifacts/confidentiality")
    output_dir.mkdir(parents=True, exist_ok=True)
    records = rows()
    columns = list(records[0])
    with (output_dir / "metadata_exposure_matrix.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    lines = ["# Metadata exposure matrix v1", "", "Generated; do not edit by hand.", "", "| " + " | ".join(columns) + " |", "|" + "|".join(["---"] * len(columns)) + "|"]
    for record in records:
        lines.append("| " + " | ".join(record[column].replace("|", "/") for column in columns) + " |")
    with (output_dir / "metadata_exposure_matrix.md").open(
        "w", encoding="utf-8", newline="\n"
    ) as stream:
        stream.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
