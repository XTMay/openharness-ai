from __future__ import annotations

from pathlib import Path

from openharness.agents.perf_agent import create_performance_plan
from openharness.agents.repo_agent import analyze_repository


def test_perf_agent_plan_uses_repo_agent_performance_targets():
    repo_root = Path(__file__).resolve().parents[3]
    example_path = repo_root / "examples" / "fastapi-service"

    manifest = analyze_repository(example_path)
    plan = create_performance_plan(manifest)

    assert plan.agent == "PerfAgent"
    assert plan.repo_agent_config == "openharness.yaml"
    assert [scenario.path for scenario in plan.scenarios] == [
        "/checkout",
        "/orders",
        "/products",
    ]
    assert all(scenario.priority == "high" for scenario in plan.scenarios)
    assert plan.scenarios[0].load_profile.virtual_users == 25
    assert plan.scenarios[0].thresholds[0].metric == "http_req_failed"


def test_perf_agent_plan_warns_when_repo_agent_has_no_targets(tmp_path):
    (tmp_path / "README.md").write_text("# docs only\n", encoding="utf-8")

    manifest = analyze_repository(tmp_path)
    plan = create_performance_plan(manifest)

    assert not plan.scenarios
    assert "RepoAgent did not find performance target candidates" in plan.warnings[0]

