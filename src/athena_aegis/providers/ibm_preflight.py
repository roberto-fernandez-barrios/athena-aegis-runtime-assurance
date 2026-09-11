"""Sanitized zero-cost IBM preflight. It never prints credentials."""

from __future__ import annotations

import argparse
import json
import os
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from athena_aegis.canonical import utc_now
from athena_aegis.providers.ibm_runtime import IBMRuntimeAdapter


TOKEN_NAMES = (
    "QISKIT_IBM_TOKEN",
    "IBM_QUANTUM_TOKEN",
    "IBM_QUANTUM_API_KEY",
    "QISKIT_IBM_RUNTIME_API_TOKEN",
)


def _usage_summary(usage: Any) -> dict[str, int | float | bool]:
    if not isinstance(usage, dict):
        return {}
    allowed_fragments = ("usage", "limit", "remaining", "second", "job")
    return {
        str(key): value
        for key, value in usage.items()
        if any(fragment in str(key).lower() for fragment in allowed_fragments)
        and isinstance(value, (int, float, bool))
    }


def run_preflight(
    token: str | None,
    source_type: str,
    channel: str,
    *,
    saved_account_available: bool = False,
) -> dict[str, Any]:
    credential_available = bool(token) or saved_account_available
    report: dict[str, Any] = {
        "schema_version": "athena-aegis.ibm-preflight/1.0.0",
        "captured_at": utc_now(),
        "credential_found": "yes" if credential_available else "no",
        "credential_source_type": source_type if credential_available else "none",
        "credential_tracked_by_git": False if source_type in ("ignored-env", "saved-account") else None,
        "contains_secret": False,
        "authentication_test": "not_attempted",
        "sdk_versions": {},
        "instance_count": None,
        "backends": [],
        "backend_contexts": [],
        "usage": None,
        "job_submitted": False,
        "scientific_evidence": False,
    }
    for package in ("qiskit", "qiskit-ibm-runtime"):
        try:
            report["sdk_versions"][package] = version(package)
        except PackageNotFoundError:
            report["sdk_versions"][package] = "not-installed"
    if not credential_available:
        return report
    try:
        adapter = IBMRuntimeAdapter(token=token, channel=channel)
        report["instance_count"] = len(adapter.service.instances())
        summaries = adapter.list_backends()
        report["backends"] = [summary.__dict__ for summary in summaries]
        context_fields = (
            "backend_id", "backend_family", "backend_version",
            "backend_calibration_timestamp", "t1_summary", "t2_summary",
            "readout_error_summary", "gate_error_summary",
            "coupling_target_digest", "queue_metadata", "scheduling_metadata",
        )
        for summary in summaries:
            try:
                context = adapter.get_backend_context(summary.backend_id)
                report["backend_contexts"].append({
                    "backend_id": summary.backend_id,
                    "fields": {
                        name: {
                            "value": context.fields[name].value,
                            "origin": context.fields[name].origin.value,
                            "trust": context.fields[name].trust.value,
                        }
                        for name in context_fields
                    },
                })
            except Exception as exc:
                report["backend_contexts"].append({
                    "backend_id": summary.backend_id,
                    "capture_error_type": type(exc).__name__,
                })
        usage = getattr(adapter.service, "usage", None)
        report["usage"] = None if usage is None else _usage_summary(usage())
        report["authentication_test"] = "pass"
    except Exception as exc:  # sanitized type only; provider message may contain account data
        report["authentication_test"] = "fail"
        report["error_type"] = type(exc).__name__
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--source-type", default="process-env")
    parser.add_argument("--channel", default="ibm_quantum_platform")
    args = parser.parse_args()
    token = next((os.environ[name] for name in TOKEN_NAMES if os.environ.get(name)), None)
    saved_account_available = False
    if token is None:
        try:
            from qiskit_ibm_runtime import QiskitRuntimeService

            saved_account_available = bool(QiskitRuntimeService.saved_accounts(channel=args.channel))
        except Exception:
            saved_account_available = False
    source_type = args.source_type if token else "saved-account"
    report = run_preflight(
        token,
        source_type,
        args.channel,
        saved_account_available=saved_account_available,
    )
    serialized = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized + "\n", encoding="utf-8")
    print(serialized)


if __name__ == "__main__":
    main()
