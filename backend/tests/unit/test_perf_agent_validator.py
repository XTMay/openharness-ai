from __future__ import annotations

from pathlib import Path

from openharness.agents.perf_agent import (
    create_performance_plan,
    generate_k6_artifacts,
    validate_k6_artifacts,
)
from openharness.agents.repo_agent import analyze_repository


def test_perf_agent_validates_generated_k6_artifacts(tmp_path):
    repo_root = Path(__file__).resolve().parents[3]
    example_path = repo_root / "examples" / "fastapi-service"
    manifest = analyze_repository(example_path)
    plan = create_performance_plan(manifest)
    generate_k6_artifacts(plan, tmp_path)

    result = validate_k6_artifacts(tmp_path)

    assert result.valid
    assert any(finding.id == "script_placeholder_payload" for finding in result.findings)


def test_perf_agent_validate_fails_for_missing_directory(tmp_path):
    result = validate_k6_artifacts(tmp_path / "missing")

    assert not result.valid
    assert result.findings[0].id == "artifacts_dir_missing"


def test_perf_agent_validate_fails_for_missing_declared_script(tmp_path):
    (tmp_path / "config.json").write_text(
        '{"scenarios": [{"name": "missing_script"}]}',
        encoding="utf-8",
    )

    result = validate_k6_artifacts(tmp_path)

    assert not result.valid
    assert any(finding.id == "k6_script_declared_missing" for finding in result.findings)


def test_perf_agent_validate_warns_for_stale_unreferenced_script(tmp_path):
    (tmp_path / "config.json").write_text(
        '{"base_url_env": "BASE_URL", "scenarios": []}',
        encoding="utf-8",
    )
    (tmp_path / "stale.js").write_text("export default function () {}\n", encoding="utf-8")

    result = validate_k6_artifacts(tmp_path)

    assert result.valid
    assert any(finding.id == "k6_script_unreferenced" for finding in result.findings)

    strict_result = validate_k6_artifacts(tmp_path, strict=True)
    assert not strict_result.valid


def test_perf_agent_validate_strict_promotes_warnings(tmp_path):
    repo_root = Path(__file__).resolve().parents[3]
    example_path = repo_root / "examples" / "fastapi-service"
    manifest = analyze_repository(example_path)
    plan = create_performance_plan(manifest)
    generate_k6_artifacts(plan, tmp_path)

    result = validate_k6_artifacts(tmp_path, strict=True)

    assert not result.valid
    assert any(finding.severity == "warning" for finding in result.findings)
