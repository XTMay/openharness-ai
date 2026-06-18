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


def test_performance_plan_schema_is_valid_json():
    repo_root = Path(__file__).resolve().parents[3]
    schema_path = repo_root / "docs" / "schemas" / "performance-plan.schema.json"

    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert schema["title"] == "OpenHarness Performance Plan"
    assert "scenarios" in schema["required"]


def test_k6_generation_result_schema_is_valid_json():
    repo_root = Path(__file__).resolve().parents[3]
    schema_path = repo_root / "docs" / "schemas" / "k6-generation-result.schema.json"

    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert schema["title"] == "OpenHarness k6 Generation Result"
    assert "files" in schema["required"]
