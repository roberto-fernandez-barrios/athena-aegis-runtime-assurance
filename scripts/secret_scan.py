"""Conservative repository secret scan used before each commit."""

from __future__ import annotations

import re
import sys
from pathlib import Path


SKIP = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache"}
TEXT_SUFFIXES = {".py", ".md", ".toml", ".json", ".yml", ".yaml", ".txt", ".csv"}
PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)(?:token|api[_-]?key|password|secret)\s*[:=]\s*['\"][A-Za-z0-9_./+=-]{20,}['\"]"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9_./+=-]{20,}"),
)


def main() -> None:
    findings: list[str] = []
    for path in Path(".").rglob("*"):
        if not path.is_file() or any(part in SKIP for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(pattern.search(text) for pattern in PATTERNS):
            findings.append(path.as_posix())
    if findings:
        print("potential secrets detected in: " + ", ".join(sorted(findings)), file=sys.stderr)
        raise SystemExit(1)
    print("secret_scan=pass")


if __name__ == "__main__":
    main()
