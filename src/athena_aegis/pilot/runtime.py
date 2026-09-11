"""Local-only configuration and sanitized pilot artifact helpers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from athena_aegis.context import ExecutionContext


@dataclass(frozen=True)
class LocalIBMConfig:
    token: str
    channel: str
    instance: str
    selected_backend: str
    pseudonym_key: bytes
    signing_key: bytes


def load_local_ibm_config(path: Path = Path(".env")) -> LocalIBMConfig:
    """Load the ignored local configuration without exposing its values."""

    if not path.is_file():
        raise RuntimeError("local ignored IBM configuration is unavailable")
    values = {
        name: value
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#") and "=" in line
        for name, value in (line.split("=", 1),)
    }
    required = (
        "IBM_QUANTUM_API_KEY",
        "IBM_QUANTUM_CHANNEL",
        "IBM_QUANTUM_INSTANCE",
        "ATHENA_AEGIS_SELECTED_BACKEND",
        "ATHENA_AEGIS_PSEUDONYM_KEY_HEX",
        "ATHENA_AEGIS_SIGNING_KEY_HEX",
    )
    if any(not values.get(name) for name in required):
        raise RuntimeError("local ignored IBM configuration is incomplete")
    try:
        pseudonym_key = bytes.fromhex(values["ATHENA_AEGIS_PSEUDONYM_KEY_HEX"])
        signing_key = bytes.fromhex(values["ATHENA_AEGIS_SIGNING_KEY_HEX"])
    except ValueError as exc:
        raise RuntimeError("local pilot key encoding is invalid") from exc
    if len(pseudonym_key) < 16 or len(signing_key) < 32:
        raise RuntimeError("local pilot keys do not meet minimum lengths")
    return LocalIBMConfig(
        values["IBM_QUANTUM_API_KEY"],
        values["IBM_QUANTUM_CHANNEL"],
        values["IBM_QUANTUM_INSTANCE"],
        values["ATHENA_AEGIS_SELECTED_BACKEND"],
        pseudonym_key,
        signing_key,
    )


def safe_usage(service: Any) -> dict[str, int | float | bool] | None:
    usage = getattr(service, "usage", None)
    if not callable(usage):
        return None
    try:
        raw = usage()
    except Exception:
        return None
    if not isinstance(raw, Mapping):
        return None
    fragments = ("usage", "limit", "remaining", "second", "job")
    return {
        str(name): value
        for name, value in raw.items()
        if isinstance(value, (int, float, bool))
        and any(fragment in str(name).lower() for fragment in fragments)
    }


def context_missingness(context: ExecutionContext) -> dict[str, Any]:
    missing = sorted(name for name, evidence in context.fields.items() if evidence.value is None)
    return {
        "field_count": len(context.fields),
        "missing_count": len(missing),
        "missing_fraction": len(missing) / len(context.fields),
        "missing_fields": missing,
    }


def oracle_metrics(observed: Any, oracle: Any) -> dict[str, float]:
    observed_array = np.asarray(observed, dtype=float)
    oracle_array = np.asarray(oracle, dtype=float)
    if observed_array.shape != oracle_array.shape:
        raise ValueError("observed and oracle matrices must have identical shape")
    delta = observed_array - oracle_array
    denominator = float(np.linalg.norm(oracle_array, ord="fro"))
    if denominator <= 0:
        raise ValueError("oracle Frobenius norm must be positive")
    return {
        "relative_frobenius_error": float(np.linalg.norm(delta, ord="fro")) / denominator,
        "mean_absolute_error": float(np.mean(np.abs(delta))),
        "maximum_absolute_error": float(np.max(np.abs(delta))),
    }


def repeat_discrepancy(first: Any, second: Any) -> dict[str, float]:
    first_array = np.asarray(first, dtype=float)
    second_array = np.asarray(second, dtype=float)
    if first_array.shape != second_array.shape:
        raise ValueError("repeat matrices must have identical shape")
    delta = first_array - second_array
    scale = max(float(np.linalg.norm(first_array, ord="fro")), 1e-15)
    return {
        "relative_frobenius_discrepancy": float(np.linalg.norm(delta, ord="fro")) / scale,
        "mean_absolute_discrepancy": float(np.mean(np.abs(delta))),
        "maximum_absolute_discrepancy": float(np.max(np.abs(delta))),
    }


def validate_no_secret_values(payload: Any, config: LocalIBMConfig) -> None:
    serialized = json.dumps(payload, sort_keys=True, default=str)
    forbidden = (
        config.token,
        config.instance,
        config.pseudonym_key.hex(),
        config.signing_key.hex(),
    )
    if any(value and value in serialized for value in forbidden):
        raise RuntimeError("secret sanitization rejected the pilot artifact")


def _pilot_path(path: Path, root: Path) -> Path:
    resolved_root = root.resolve()
    pilot_root = (resolved_root / "artifacts" / "pilot").resolve()
    resolved = path.resolve() if path.is_absolute() else (resolved_root / path).resolve()
    try:
        relative = resolved.relative_to(pilot_root)
    except ValueError as exc:
        raise ValueError("pilot outputs must remain under artifacts/pilot") from exc
    if "confirmatory" in {part.lower() for part in relative.parts}:
        raise ValueError("pilot outputs cannot enter a confirmatory namespace")
    return resolved


def write_pilot_json(path: Path, payload: Mapping[str, Any], *, root: Path = Path(".")) -> Path:
    if payload.get("phase") != "pilot" or payload.get("scientific_evidence") is not False:
        raise ValueError("every pilot artifact must declare phase=pilot and scientific_evidence=false")
    target = _pilot_path(path, root)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    temporary.replace(target)
    return target


def write_pilot_manifest(*, root: Path = Path(".")) -> Path:
    pilot_root = (root.resolve() / "artifacts" / "pilot")
    entries = []
    for path in sorted(pilot_root.rglob("*")):
        if (
            not path.is_file()
            or path.name == "manifest.v1.json"
            or any(part in {"private", "raw"} for part in path.relative_to(pilot_root).parts)
        ):
            continue
        entries.append(
            {
                "path": path.relative_to(root.resolve()).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    payload = {
        "schema_version": "athena-aegis.pilot-manifest/1.0.0",
        "phase": "pilot",
        "scientific_evidence": False,
        "files": entries,
    }
    return write_pilot_json(Path("artifacts/pilot/manifest.v1.json"), payload, root=root)
