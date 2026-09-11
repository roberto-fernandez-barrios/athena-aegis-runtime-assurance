"""Sanitized zero-cost IBM preflight. It never prints credentials."""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from athena_aegis.canonical import utc_now
from athena_aegis.providers.ibm_runtime import IBMRuntimeAdapter
from athena_aegis.providers.selection import select_pilot_backend


TOKEN_NAMES = (
    "QISKIT_IBM_TOKEN",
    "IBM_QUANTUM_TOKEN",
    "IBM_QUANTUM_API_KEY",
    "QISKIT_IBM_RUNTIME_API_TOKEN",
)
TOKEN_FORMAT = re.compile(r"^[A-Za-z0-9_-]{20,}$")


def _load_ignored_env(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    allowed = set(TOKEN_NAMES) | {
        "IBM_QUANTUM_CHANNEL",
        "IBM_QUANTUM_INSTANCE",
        "ATHENA_AEGIS_SELECTED_BACKEND",
    }
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, value = stripped.split("=", 1)
        if name in allowed and value:
            values[name] = value
    return values


def _failure_details(exc: Exception) -> tuple[str, str]:
    """Map provider errors to a fixed vocabulary without persisting messages."""

    message = str(exc).lower()
    if any(term in message for term in ("proxy", "tunnel connection", "proxyerror")):
        return "proxy/network", "network path failed before IBM authentication completed"
    if any(term in message for term in ("ssl", "certificate", "tls")):
        return "proxy/network/TLS", "TLS validation failed before IBM authentication completed"
    if any(
        term in message
        for term in ("timed out", "timeout", "connection", "name resolution", "temporarily unavailable")
    ):
        return "endpoint/network", "IBM endpoint could not be reached reliably"
    if any(
        term in message
        for term in ("401", "unauthorized", "invalid token", "api key not valid", "authentication failed")
    ):
        return "token rejected", "IBM rejected the supplied API key"
    if any(term in message for term in ("no matching instance", "unable to find account", "instance")):
        return "instance/entitlement", "authentication did not resolve a matching accessible instance"
    if any(term in message for term in ("channel", "ibm_cloud", "ibm_quantum_platform")):
        return "channel/configuration", "runtime channel or account configuration was rejected"
    return "other", f"IBM Runtime raised {type(exc).__name__} during read-only authentication"


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
    instance: str | None = None,
    saved_account_available: bool = False,
) -> dict[str, Any]:
    credential_available = bool(token) or saved_account_available
    report: dict[str, Any] = {
        "schema_version": "athena-aegis.ibm-preflight/1.0.0",
        "captured_at": utc_now(),
        "phase": "preflight",
        "credential_present": "yes" if credential_available else "no",
        "credential_source_type": source_type if credential_available else "none",
        "sdk_version": "not-installed",
        "qiskit_version": "not-installed",
        "channel": channel,
        "instance_present": "yes" if instance else "no",
        "authentication_result": "not_attempted",
        "failure_category": "none",
        "sanitized_error": "none",
        "instance_count": None,
        "backends": [],
        "backend_contexts": [],
        "backend_selection": None,
        "usage": None,
        "job_submitted": False,
        "scientific_evidence": False,
    }
    for package, key in (("qiskit", "qiskit_version"), ("qiskit-ibm-runtime", "sdk_version")):
        try:
            report[key] = version(package)
        except PackageNotFoundError:
            report[key] = "not-installed"
    if not credential_available:
        report["failure_category"] = "token absent"
        report["sanitized_error"] = "credential not present"
        return report
    if token and not TOKEN_FORMAT.fullmatch(token):
        report["authentication_result"] = "fail"
        report["failure_category"] = "token malformed"
        report["sanitized_error"] = "credential format failed local validation"
        return report
    previous_disable = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        adapter = IBMRuntimeAdapter(token=token, channel=channel, instance=instance)
        report["instance_count"] = len(adapter.service.instances())
        summaries = adapter.list_backends()
        report["backends"] = [summary.__dict__ for summary in summaries]
        selection = select_pilot_backend(summaries, required_qubits=2)
        report["backend_selection"] = {
            "rule": selection.rule,
            "required_qubits": selection.required_qubits,
            "candidate_backends": [item.backend_id for item in selection.candidates],
            "eligible_backends": [item.backend_id for item in selection.eligible],
            "selected_backend": selection.selected.backend_id,
            "selection_timestamp": report["captured_at"],
        }
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
        report["authentication_result"] = "pass"
    except Exception as exc:
        category, sanitized_error = _failure_details(exc)
        report["authentication_result"] = "fail"
        report["failure_category"] = category
        report["sanitized_error"] = sanitized_error
    finally:
        logging.disable(previous_disable)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--channel")
    parser.add_argument("--instance")
    args = parser.parse_args()
    local = _load_ignored_env(args.env_file)
    process_token = next((os.environ[name] for name in TOKEN_NAMES if os.environ.get(name)), None)
    local_token = next((local[name] for name in TOKEN_NAMES if local.get(name)), None)
    token = process_token or local_token
    source_type = "process-env" if process_token else ("ignored-env" if local_token else "none")
    channel = args.channel or os.environ.get("IBM_QUANTUM_CHANNEL") or local.get(
        "IBM_QUANTUM_CHANNEL", "ibm_quantum_platform"
    )
    instance = args.instance or os.environ.get("IBM_QUANTUM_INSTANCE") or local.get(
        "IBM_QUANTUM_INSTANCE"
    )
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService

        saved_account_available = bool(QiskitRuntimeService.saved_accounts(channel=channel))
    except Exception:
        saved_account_available = False
    report = run_preflight(
        token,
        source_type,
        channel,
        instance=instance,
        saved_account_available=False,
    )
    if report["authentication_result"] == "fail" and saved_account_available:
        fallback = run_preflight(
            None,
            "saved-account",
            channel,
            saved_account_available=True,
        )
        if fallback["authentication_result"] == "pass":
            report = fallback
    serialized = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized + "\n", encoding="utf-8")
    print(serialized)


if __name__ == "__main__":
    main()
