"""Data models for RepoAgent repository analysis."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class RepositoryIdentity:
    root: str
    current_branch: str | None = None
    commit_sha: str | None = None


@dataclass(frozen=True)
class RepositoryConfiguration:
    path: str | None = None
    ignore: list[str] = field(default_factory=list)
    service_roots: list[str] = field(default_factory=list)
    production_paths: list[str] = field(default_factory=list)
    business_critical_keywords: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class LanguageStat:
    name: str
    files: int
    bytes: int


@dataclass(frozen=True)
class DetectionEvidence:
    source: str
    detail: str
    line: int | None = None


@dataclass(frozen=True)
class FrameworkDetection:
    name: str
    confidence: str
    evidence: list[DetectionEvidence] = field(default_factory=list)


@dataclass(frozen=True)
class ServiceEntrypoint:
    kind: str
    path: str
    name: str | None = None
    command: str | None = None
    confidence: str = "medium"
    evidence: list[DetectionEvidence] = field(default_factory=list)


@dataclass(frozen=True)
class ApiRoute:
    method: str
    path: str
    source: str
    framework: str
    confidence: str = "medium"
    evidence: list[DetectionEvidence] = field(default_factory=list)


@dataclass(frozen=True)
class PerformanceTarget:
    method: str
    path: str
    source: str
    framework: str
    priority: str
    reason: str
    evidence: list[DetectionEvidence] = field(default_factory=list)


@dataclass(frozen=True)
class RepositoryManifest:
    repository: RepositoryIdentity
    configuration: RepositoryConfiguration
    generated_at: str
    total_files: int
    total_bytes: int
    languages: list[LanguageStat] = field(default_factory=list)
    package_managers: list[str] = field(default_factory=list)
    frameworks: list[FrameworkDetection] = field(default_factory=list)
    service_entrypoints: list[ServiceEntrypoint] = field(default_factory=list)
    api_routes: list[ApiRoute] = field(default_factory=list)
    performance_targets: list[PerformanceTarget] = field(default_factory=list)
    infrastructure: list[str] = field(default_factory=list)
    test_inventory: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
