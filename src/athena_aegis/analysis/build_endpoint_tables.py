"""Build rate endpoint tables from normalized JSONL service records."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from athena_aegis.analysis.metrics import wilson_rate


ENDPOINTS = {
    "unsafe_continuation_rate": ("unsafe_eligible", "unsafe_continuation", "service request"),
    "false_hold_rate": ("supported_correct", "false_hold", "service request"),
    "recovery_success_rate": ("recovery_attempted", "recovery_success", "recovery attempt"),
    "fallback_correctness": ("fallback_executed", "fallback_correct", "fallback execution"),
    "service_availability": ("eligible_request", "available_correct_within_deadline", "service request"),
    "context_oos_detection": ("context_oos", "abstained_before_calibration", "execution context"),
    "calibration_validity_violation": ("calibrated_assertion", "validity_violation", "test unit"),
    "decision_error_after_context_shift": ("post_shift", "decision_error", "service request"),
}


def build(records: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for endpoint, (eligible_name, event_name, unit) in ENDPOINTS.items():
        eligible = [record for record in records if record.get(eligible_name) is True]
        if not eligible:
            rows.append({"endpoint": endpoint, "numerator": 0, "denominator": 0, "estimate": None, "lower": None, "upper": None, "experimental_unit": unit})
            continue
        estimate = wilson_rate(sum(record.get(event_name) is True for record in eligible), len(eligible), unit)
        rows.append({"endpoint": endpoint, **estimate.__dict__})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    records = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows = build(records)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
