"""Permanent fail-closed verifier of Campaign A byte identity (author decision 18).

Campaign A evidence lives under ``artifacts/confirmatory/campaign/``.  Campaign B
code must never write there; every Campaign B writer calls
:func:`guard_write_path`, and every development verification, freeze, runner
preflight and final analysis calls :func:`verify_campaign_a_immutable`.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

CAMPAIGN_A_RELATIVE = Path("artifacts/confirmatory/campaign")
BASELINE_RELATIVE = Path("configs/campaign_b/campaign_a_baseline.v1.json")
BASELINE_SCHEMA_VERSION = "athena-aegis.campaign-a-baseline/1.0.0"
ALLOWED_UNTRACKED = ("STOP",)


class CampaignAImmutabilityError(RuntimeError):
    """Campaign A evidence differs from its sealed baseline, or a write was attempted."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def guard_write_path(path: Path, repo_root: Path) -> Path:
    """Refuse any path that resolves inside the Campaign A evidence namespace."""

    resolved = Path(path).resolve()
    forbidden = (Path(repo_root) / CAMPAIGN_A_RELATIVE).resolve()
    if resolved == forbidden or forbidden in resolved.parents:
        raise CampaignAImmutabilityError(f"write refused: {resolved} is inside the sealed Campaign A namespace")
    return resolved


def _git(repo_root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(["git", *args], cwd=repo_root, capture_output=True, text=True, check=False)
    except (OSError, FileNotFoundError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def build_baseline(repo_root: Path) -> dict[str, Any]:
    """Build the pinned baseline from the git-tracked Campaign A files (used once, pre-freeze)."""

    repo_root = Path(repo_root)
    listing = _git(repo_root, "ls-files", "-z", CAMPAIGN_A_RELATIVE.as_posix())
    if listing is None:
        raise CampaignAImmutabilityError("git is required to build the Campaign A baseline")
    files = []
    for relative in sorted(item for item in listing.split("\0") if item):
        path = repo_root / relative
        files.append({"path": relative.replace("\\", "/"), "bytes": path.stat().st_size, "sha256": _sha256(path)})
    tree = (_git(repo_root, "rev-parse", f"HEAD:{CAMPAIGN_A_RELATIVE.as_posix()}") or "").strip()
    head = (_git(repo_root, "rev-parse", "HEAD") or "").strip()
    listing_digest = hashlib.sha256("".join(f"{item['sha256']}  {item['path']}\n" for item in files).encode()).hexdigest()
    return {
        "schema_version": BASELINE_SCHEMA_VERSION,
        "campaign_a_directory": CAMPAIGN_A_RELATIVE.as_posix(),
        "baseline_taken_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "baseline_head_commit": head,
        "git_tree_hash": tree,
        "tracked_file_count": len(files),
        "tracked_listing_sha256": listing_digest,
        "allowed_untracked_files": list(ALLOWED_UNTRACKED),
        "files": files,
    }


def load_baseline(repo_root: Path) -> dict[str, Any]:
    path = Path(repo_root) / BASELINE_RELATIVE
    if not path.is_file():
        raise CampaignAImmutabilityError(f"Campaign A baseline missing: {BASELINE_RELATIVE}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != BASELINE_SCHEMA_VERSION:
        raise CampaignAImmutabilityError("Campaign A baseline schema version mismatch")
    return payload


def verify_campaign_a_immutable(
    repo_root: Path,
    baseline: Mapping[str, Any] | None = None,
    *,
    campaign_a_dir: Path | None = None,
    require_git: bool = True,
) -> dict[str, Any]:
    """Verify every pinned file byte-identical and nothing added, removed or modified.

    Raises :class:`CampaignAImmutabilityError` on the first discrepancy (fail-closed).
    Returns a report that callers may record in their own namespace.
    """

    repo_root = Path(repo_root)
    baseline = dict(baseline) if baseline is not None else load_baseline(repo_root)
    directory = Path(campaign_a_dir) if campaign_a_dir is not None else repo_root / CAMPAIGN_A_RELATIVE
    if not directory.is_dir():
        raise CampaignAImmutabilityError(f"Campaign A directory missing: {directory}")
    problems: list[str] = []
    pinned = {item["path"]: item for item in baseline["files"]}
    for relative, item in pinned.items():
        path = directory / Path(relative).relative_to(CAMPAIGN_A_RELATIVE) if relative.startswith(CAMPAIGN_A_RELATIVE.as_posix()) else directory / relative
        if not path.is_file():
            problems.append(f"missing: {relative}")
            continue
        if path.stat().st_size != item["bytes"] or _sha256(path) != item["sha256"]:
            problems.append(f"modified: {relative}")
    allowed_untracked = set(baseline.get("allowed_untracked_files", ALLOWED_UNTRACKED))
    observed = 0
    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        observed += 1
        relative = (CAMPAIGN_A_RELATIVE / path.relative_to(directory)).as_posix()
        if relative in pinned:
            continue
        if path.relative_to(directory).as_posix() in allowed_untracked:
            continue
        problems.append(f"unexpected file: {relative}")
    git_tree = None
    git_status_lines: list[str] = []
    if require_git and campaign_a_dir is None:
        git_tree = (_git(repo_root, "rev-parse", f"HEAD:{CAMPAIGN_A_RELATIVE.as_posix()}") or "").strip() or None
        if git_tree is None:
            problems.append("git tree hash unavailable")
        elif git_tree != baseline["git_tree_hash"]:
            problems.append(f"git tree hash changed: {git_tree} != {baseline['git_tree_hash']}")
        status = _git(repo_root, "status", "--porcelain", "--", CAMPAIGN_A_RELATIVE.as_posix())
        if status is None:
            problems.append("git status unavailable")
        else:
            for line in status.splitlines():
                if not line.strip():
                    continue
                git_status_lines.append(line)
                code, _, name = line.partition(" ")
                name = name.strip().replace("\\", "/")
                if code.strip() == "??" and Path(name).name in allowed_untracked and name.startswith(CAMPAIGN_A_RELATIVE.as_posix()):
                    continue
                problems.append(f"git working tree change: {line}")
    report = {
        "verified_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "campaign_a_directory": directory.as_posix(),
        "pinned_files": len(pinned),
        "observed_files": observed,
        "git_tree_hash": git_tree,
        "baseline_git_tree_hash": baseline["git_tree_hash"],
        "baseline_tracked_listing_sha256": baseline["tracked_listing_sha256"],
        "git_status": git_status_lines,
        "byte_identical": not problems,
        "problems": problems,
    }
    if problems:
        raise CampaignAImmutabilityError("Campaign A immutability violated: " + "; ".join(problems[:10]))
    return report
