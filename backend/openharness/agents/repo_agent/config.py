"""Configuration support for RepoAgent."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

CONFIG_FILENAMES = ("openharness.yaml", "openharness.yml")
DEFAULT_BUSINESS_CRITICAL_KEYWORDS = (
    "checkout",
    "payment",
    "order",
    "search",
    "cart",
    "booking",
)


@dataclass(frozen=True)
class RepoAgentConfig:
    path: str | None = None
    ignore: list[str] = field(default_factory=list)
    service_roots: list[str] = field(default_factory=list)
    production_paths: list[str] = field(default_factory=list)
    business_critical_keywords: list[str] = field(
        default_factory=lambda: list(DEFAULT_BUSINESS_CRITICAL_KEYWORDS)
    )


def load_repo_agent_config(root: Path) -> RepoAgentConfig:
    config_path = _find_config_path(root)
    if config_path is None:
        return RepoAgentConfig()

    try:
        raw_config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {config_path}: {exc}") from exc

    if not isinstance(raw_config, dict):
        raise ValueError(f"RepoAgent config must be a YAML mapping: {config_path}")

    performance = _mapping(raw_config.get("performance"))
    labels = _mapping(raw_config.get("labels"))

    business_keywords = _string_list(
        performance.get("business_critical_keywords")
        or labels.get("business_critical")
        or DEFAULT_BUSINESS_CRITICAL_KEYWORDS
    )

    return RepoAgentConfig(
        path=config_path.relative_to(root).as_posix(),
        ignore=_string_list(raw_config.get("ignore")),
        service_roots=_normalize_prefixes(_string_list(raw_config.get("service_roots"))),
        production_paths=_normalize_prefixes(_string_list(raw_config.get("production_paths"))),
        business_critical_keywords=[keyword.lower() for keyword in business_keywords],
    )


def _find_config_path(root: Path) -> Path | None:
    for filename in CONFIG_FILENAMES:
        candidate = root / filename
        if candidate.is_file():
            return candidate
    return None


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _normalize_prefixes(paths: list[str]) -> list[str]:
    normalized: list[str] = []
    for path in paths:
        cleaned = path.strip().strip("/")
        if cleaned:
            normalized.append(cleaned)
    return normalized

