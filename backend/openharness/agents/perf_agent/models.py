"""Data models for PerfAgent planning."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class LoadProfile:
    name: str
    virtual_users: int
    duration: str
    ramp_up: str
    description: str


@dataclass(frozen=True)
class Threshold:
    metric: str
    condition: str
    rationale: str


@dataclass(frozen=True)
class PerformanceScenario:
    name: str
    method: str
    path: str
    priority: str
    source: str
    framework: str
    reason: str
    load_profile: LoadProfile
    thresholds: list[Threshold] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PerformancePlan:
    agent: str
    repository_root: str
    repo_agent_config: str | None
    generated_from: str
    base_url_env: str
    scenarios: list[PerformanceScenario] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

