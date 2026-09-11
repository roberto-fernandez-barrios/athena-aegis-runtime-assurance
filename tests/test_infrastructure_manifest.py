import json
from pathlib import Path

from athena_aegis.analysis.build_manifest import repository_files


def test_manifest_candidates_exclude_ignored_build_and_environment_debris():
    paths = {path.as_posix() for path in repository_files()}
    assert ".gitattributes" in paths
    assert all(".egg-info/" not in path for path in paths)
    assert all(".venv" not in path for path in paths)
    assert all("__pycache__" not in path for path in paths)


def test_generated_manifest_has_no_environment_specific_paths():
    manifest = json.loads(
        Path("artifacts/manifests/infrastructure_manifest.v1.json").read_text(encoding="utf-8")
    )
    paths = {entry["path"] for entry in manifest["files"]}
    assert all(".egg-info/" not in path for path in paths)
    assert all(".venv" not in path for path in paths)
