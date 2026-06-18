"""PerfAgent planning logic."""

from __future__ import annotations

from openharness.agents.perf_agent.models import (
    LoadProfile,
    PerformancePlan,
    PerformanceScenario,
    Threshold,
)
from openharness.agents.repo_agent.models import PerformanceTarget, RepositoryManifest


def create_performance_plan(
    manifest: RepositoryManifest, max_scenarios: int = 5
) -> PerformancePlan:
    targets = manifest.performance_targets[:max_scenarios]
    warnings: list[str] = []

    if not manifest.performance_targets:
        warnings.append(
            "RepoAgent did not find performance target candidates. "
            "Add API routes or configure openharness.yaml service_roots."
        )

    return PerformancePlan(
        agent="PerfAgent",
        repository_root=manifest.repository.root,
        repo_agent_config=manifest.configuration.path,
        generated_from="RepoAgent performance_targets",
        base_url_env="BASE_URL",
        scenarios=[_scenario_from_target(target) for target in targets],
        assumptions=[
            "The target service is running before executing generated load tests.",
            "BASE_URL will point to a non-production environment unless explicitly approved.",
            "Authentication, seed data, and tenant context may need project-specific setup.",
        ],
        warnings=warnings,
    )


def _scenario_from_target(target: PerformanceTarget) -> PerformanceScenario:
    return PerformanceScenario(
        name=_scenario_name(target),
        method=target.method,
        path=target.path,
        priority=target.priority,
        source=target.source,
        framework=target.framework,
        reason=target.reason,
        load_profile=_load_profile(target),
        thresholds=_thresholds(target),
        assumptions=_target_assumptions(target),
    )


def _scenario_name(target: PerformanceTarget) -> str:
    cleaned_path = target.path.strip("/").replace("/", "_") or "root"
    return f"{target.method.lower()}_{cleaned_path}"


def _load_profile(target: PerformanceTarget) -> LoadProfile:
    if target.priority == "high":
        return LoadProfile(
            name="baseline-load",
            virtual_users=25,
            duration="3m",
            ramp_up="30s",
            description="Baseline user-facing load for a high-priority route.",
        )

    if target.priority == "medium":
        return LoadProfile(
            name="light-load",
            virtual_users=10,
            duration="2m",
            ramp_up="20s",
            description="Light exploratory load for a medium-priority route.",
        )

    return LoadProfile(
        name="smoke-load",
        virtual_users=1,
        duration="30s",
        ramp_up="0s",
        description="Smoke-level load to validate script behavior.",
    )


def _thresholds(target: PerformanceTarget) -> list[Threshold]:
    latency_condition = "p(95)<500"
    if target.method == "GET" and target.priority == "high":
        latency_condition = "p(95)<350"

    return [
        Threshold(
            metric="http_req_failed",
            condition="rate<0.01",
            rationale="Keep request failure rate under 1%.",
        ),
        Threshold(
            metric="http_req_duration",
            condition=latency_condition,
            rationale="Keep p95 latency within an initial user-facing budget.",
        ),
    ]


def _target_assumptions(target: PerformanceTarget) -> list[str]:
    assumptions = [f"Route was selected from RepoAgent evidence in {target.source}."]
    if target.method in {"POST", "PUT", "PATCH", "DELETE"}:
        assumptions.append("Write scenario may require safe test data and idempotency controls.")
    return assumptions

