"""Build a deterministic SHA-256 manifest of scientific infrastructure."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOTS = ("configs", "schemas", "docs", "manuscript", "experiments", "src", "tests", "scripts", ".github")
TOP_LEVEL = (
    ".gitattributes",
    ".gitignore",
    "pyproject.toml",
    "requirements-lock.txt",
    "README.md",
    "LICENSE",
)


def repository_files() -> list[Path]:
    """Return tracked and non-ignored pending files, independent of build debris."""

    completed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        check=True,
        capture_output=True,
    )
    candidates = [
        Path(value.decode("utf-8"))
        for value in completed.stdout.split(b"\0")
        if value
    ]
    roots = set(ROOTS)
    top_level = set(TOP_LEVEL)
    return [
        path
        for path in candidates
        if path.as_posix() in top_level or (path.parts and path.parts[0] in roots)
    ]


def main() -> None:
    files = repository_files()
    entries = []
    for path in sorted(set(files), key=lambda item: item.as_posix()):
        entries.append({
            "path": path.as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size,
        })
    output = Path("artifacts/manifests/infrastructure_manifest.v1.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(
            json.dumps(
                {
                    "schema_version": "athena-aegis.infrastructure-manifest/1.0.0",
                    "files": entries,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )


if __name__ == "__main__":
    main()
