from __future__ import annotations

import json
from pathlib import Path

from openharness.agents.perf_agent import create_performance_plan, generate_k6_artifacts
from openharness.agents.repo_agent import analyze_repository


def test_perf_agent_generates_reviewable_k6_artifacts(tmp_path):
    repo_root = Path(__file__).resolve().parents[3]
    example_path = repo_root / "examples" / "fastapi-service"
    manifest = analyze_repository(example_path)
    plan = create_performance_plan(manifest)

    result = generate_k6_artifacts(plan, tmp_path)

    generated_names = {Path(file.path).name for file in result.files}
    assert {
        "post_checkout.js",
        "post_orders.js",
        "get_products.js",
        "config.json",
        "README.md",
    }.issubset(generated_names)

    checkout_script = (tmp_path / "post_checkout.js").read_text(encoding="utf-8")
    assert "const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';" in checkout_script
    assert "const response = http.post(" in checkout_script
    assert "`${BASE_URL}/checkout`" in checkout_script
    assert "JSON.stringify(payload)" in checkout_script
    assert "http_req_failed" in checkout_script
    assert "p(95)<500" in checkout_script

    config = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert config["base_url_env"] == "BASE_URL"
    assert config["scenarios"][0]["path"] == "/checkout"


def test_perf_agent_generate_handles_empty_plan(tmp_path):
    manifest = analyze_repository(tmp_path)
    plan = create_performance_plan(manifest)

    result = generate_k6_artifacts(plan, tmp_path)

    assert result.warnings
    assert (tmp_path / "config.json").exists()
    assert not list(tmp_path.glob("*.js"))
