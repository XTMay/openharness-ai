"""Filesystem scanning utilities for RepoAgent."""

from __future__ import annotations

import os
from dataclasses import dataclass
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


def scan_repository(root: Path, max_files: int = 10_000) -> ScanResult:
    root = root.resolve()
    files: list[FileRecord] = []
    reached_file_limit = False

    for current_root, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            dirname for dirname in dirnames if dirname not in IGNORED_DIR_NAMES
        )

        current_path = Path(current_root)
        for filename in sorted(filenames):
            absolute_path = current_path / filename
            if not absolute_path.is_file():
                continue

            try:
                size = absolute_path.stat().st_size
            except OSError:
                continue

            files.append(
                FileRecord(
                    path=absolute_path,
                    relative_path=absolute_path.relative_to(root).as_posix(),
                    size=size,
                )
            )

            if len(files) >= max_files:
                reached_file_limit = True
                return ScanResult(root=root, files=files, reached_file_limit=reached_file_limit)

    return ScanResult(root=root, files=files, reached_file_limit=reached_file_limit)

