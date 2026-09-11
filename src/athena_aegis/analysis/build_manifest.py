"""Build a deterministic SHA-256 manifest of scientific infrastructure."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOTS = ("configs", "schemas", "docs", "manuscript", "experiments", "src", "tests", "scripts", ".github")
TOP_LEVEL = ("pyproject.toml", "requirements-lock.txt", "README.md", "LICENSE")


def main() -> None:
    files = [Path(name) for name in TOP_LEVEL]
    for root in ROOTS:
        files.extend(path for path in Path(root).rglob("*") if path.is_file() and "__pycache__" not in path.parts)
    entries = []
    for path in sorted(set(files), key=lambda item: item.as_posix()):
        entries.append({
            "path": path.as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size,
        })
    output = Path("artifacts/manifests/infrastructure_manifest.v1.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"schema_version": "athena-aegis.infrastructure-manifest/1.0.0", "files": entries}, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
