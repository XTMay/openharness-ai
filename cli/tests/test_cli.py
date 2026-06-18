from __future__ import annotations

import json

from openharness_cli.main import main


def test_analyze_cli_outputs_json(tmp_path, capsys):
    (tmp_path / "app.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/health')\ndef health(): pass\n",
        encoding="utf-8",
    )

    exit_code = main(["analyze", "--repo", str(tmp_path), "--format", "json"])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["frameworks"] == ["FastAPI"]
    assert output["api_routes"][0]["path"] == "/health"


def test_analyze_cli_returns_error_for_missing_repo(capsys):
    exit_code = main(["analyze", "--repo", "/path/that/does/not/exist"])

    assert exit_code == 2
    assert "does not exist" in capsys.readouterr().err

