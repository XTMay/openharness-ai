from __future__ import annotations

import json
from pathlib import Path

from openharness_cli.main import main


def _example_repo_path() -> Path:
    return Path(__file__).resolve().parents[2] / "examples" / "fastapi-service"


def test_analyze_cli_outputs_json(tmp_path, capsys):
    (tmp_path / "app.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/health')\ndef health(): pass\n",
        encoding="utf-8",
    )

    exit_code = main(["analyze", "--repo", str(tmp_path), "--format", "json"])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["configuration"]["path"] is None
    assert output["frameworks"][0]["name"] == "FastAPI"
    assert output["frameworks"][0]["evidence"][0]["source"] == "app.py"
    assert output["api_routes"][0]["path"] == "/health"


def test_analyze_cli_outputs_markdown(tmp_path, capsys):
    (tmp_path / "app.py").write_text(
        "from fastapi import FastAPI\n"
        "app = FastAPI()\n"
        "@app.post('/checkout')\n"
        "def checkout(): pass\n",
        encoding="utf-8",
    )

    exit_code = main(["analyze", "--repo", str(tmp_path), "--format", "markdown"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "# OpenHarness RepoAgent Report" in output
    assert "| `POST` | `/checkout` | FastAPI |" in output
    assert "Business-critical route keyword" in output


def test_analyze_cli_returns_error_for_missing_repo(capsys):
    exit_code = main(["analyze", "--repo", "/path/that/does/not/exist"])

    assert exit_code == 2
    assert "does not exist" in capsys.readouterr().err


def test_analyze_cli_returns_error_for_invalid_config(tmp_path, capsys):
    (tmp_path / "openharness.yaml").write_text("ignore: [broken\n", encoding="utf-8")

    exit_code = main(["analyze", "--repo", str(tmp_path)])

    assert exit_code == 2
    assert "Invalid YAML" in capsys.readouterr().err


def test_perf_plan_cli_outputs_markdown_for_example(capsys):
    exit_code = main(["perf", "plan", "--repo", str(_example_repo_path()), "--format", "markdown"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "# OpenHarness PerfAgent Plan" in output
    assert "| high | `POST` | `/checkout` |" in output
    assert "RepoAgent config: `openharness.yaml`" in output


def test_perf_plan_cli_outputs_json_for_example(capsys):
    exit_code = main(["perf", "plan", "--repo", str(_example_repo_path()), "--format", "json"])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["agent"] == "PerfAgent"
    assert output["scenarios"][0]["path"] == "/checkout"


def test_perf_generate_cli_writes_k6_artifacts(tmp_path, capsys):
    output_dir = tmp_path / "k6"

    exit_code = main(
        [
            "perf",
            "generate",
            "--repo",
            str(_example_repo_path()),
            "--output",
            str(output_dir),
            "--format",
            "json",
        ]
    )

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["output_dir"] == output_dir.resolve().as_posix()
    assert (output_dir / "post_checkout.js").exists()
    assert (output_dir / "config.json").exists()


def test_perf_validate_cli_checks_generated_artifacts(tmp_path, capsys):
    output_dir = tmp_path / "k6"
    main(
        [
            "perf",
            "generate",
            "--repo",
            str(_example_repo_path()),
            "--output",
            str(output_dir),
        ]
    )
    capsys.readouterr()

    exit_code = main(
        [
            "perf",
            "validate",
            "--artifacts",
            str(output_dir),
            "--format",
            "text",
        ]
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Status: PASS" in output
    assert "WARNING script_placeholder_payload" in output


def test_perf_validate_cli_fails_for_missing_artifacts(tmp_path, capsys):
    exit_code = main(["perf", "validate", "--artifacts", str(tmp_path / "missing")])

    assert exit_code == 1
    output = capsys.readouterr().out
    assert "artifacts_dir_missing" in output


def test_perf_validate_cli_strict_fails_on_warnings(tmp_path, capsys):
    output_dir = tmp_path / "k6"
    main(
        [
            "perf",
            "generate",
            "--repo",
            str(_example_repo_path()),
            "--output",
            str(output_dir),
        ]
    )
    capsys.readouterr()

    exit_code = main(["perf", "validate", "--artifacts", str(output_dir), "--strict"])

    assert exit_code == 1
    output = capsys.readouterr().out
    assert "script_placeholder_payload" in output
