from __future__ import annotations

import json
from pathlib import Path


def test_repository_manifest_schema_is_valid_json():
    repo_root = Path(__file__).resolve().parents[3]
    schema_path = repo_root / "docs" / "schemas" / "repository-manifest.schema.json"

    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert schema["title"] == "OpenHarness Repository Manifest"
    assert "configuration" in schema["required"]
    assert "performance_targets" in schema["required"]
