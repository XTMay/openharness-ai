"""Filesystem scanning utilities for RepoAgent."""

from __future__ import annotations

import os
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

IGNORED_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".mypy_cache",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    ".vscode",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "htmlcov",
    "node_modules",
    "target",
    "vendor",
    "venv",
}


@dataclass(frozen=True)
class FileRecord:
    path: Path
    relative_path: str
    size: int


@dataclass(frozen=True)
class ScanResult:
    root: Path
    files: list[FileRecord]
    reached_file_limit: bool


def scan_repository(
    root: Path, max_files: int = 10_000, ignore_patterns: list[str] | None = None
) -> ScanResult:
    root = root.resolve()
    files: list[FileRecord] = []
    reached_file_limit = False
    ignore_patterns = ignore_patterns or []

    for current_root, dirnames, filenames in os.walk(root):
        current_path = Path(current_root)
        dirnames[:] = sorted(
            dirname
            for dirname in dirnames
            if dirname not in IGNORED_DIR_NAMES
            and not _matches_ignore(
                (current_path / dirname).relative_to(root).as_posix(),
                ignore_patterns,
                is_dir=True,
            )
        )

        for filename in sorted(filenames):
            absolute_path = current_path / filename
            if not absolute_path.is_file():
                continue
            relative_path = absolute_path.relative_to(root).as_posix()
            if _matches_ignore(relative_path, ignore_patterns, is_dir=False):
                continue

            try:
                size = absolute_path.stat().st_size
            except OSError:
                continue

            files.append(
                FileRecord(
                    path=absolute_path,
                    relative_path=relative_path,
                    size=size,
                )
            )

            if len(files) >= max_files:
                reached_file_limit = True
                return ScanResult(root=root, files=files, reached_file_limit=reached_file_limit)

    return ScanResult(root=root, files=files, reached_file_limit=reached_file_limit)


def _matches_ignore(relative_path: str, ignore_patterns: list[str], is_dir: bool) -> bool:
    candidates = [relative_path]
    if is_dir:
        candidates.append(f"{relative_path}/")
    for pattern in ignore_patterns:
        normalized = pattern.strip().lstrip("/")
        if not normalized:
            continue
        if normalized.endswith("/**") and relative_path.startswith(normalized[:-3].rstrip("/")):
            return True
        if any(fnmatch(candidate, normalized) for candidate in candidates):
            return True
    return False
