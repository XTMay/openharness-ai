"""OpenHarness command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TextIO

from openharness import __version__
from openharness.agents.repo_agent import analyze_repository
from openharness.agents.repo_agent.models import RepositoryManifest


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "analyze":
        return _run_analyze(args, stdout=sys.stdout, stderr=sys.stderr)

    parser.print_help()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="openharness",
        description="OpenHarness AI developer tools.",
    )
    parser.add_argument("--version", action="version", version=f"openharness {__version__}")

    subcommands = parser.add_subparsers(dest="command")
    analyze = subcommands.add_parser(
        "analyze",
        help="Analyze a repository and print a RepoAgent manifest.",
    )
    analyze.add_argument(
        "--repo",
        default=".",
        help="Repository path to analyze. Defaults to the current directory.",
    )
    analyze.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format. Defaults to json.",
    )
    analyze.add_argument(
        "--output",
        help="Optional output file. Parent directories must already exist.",
    )
    analyze.add_argument(
        "--max-files",
        type=int,
        default=10_000,
        help="Maximum number of files to scan before stopping.",
    )

    return parser


def _run_analyze(args: argparse.Namespace, stdout: TextIO, stderr: TextIO) -> int:
    try:
        manifest = analyze_repository(args.repo, max_files=args.max_files)
    except (FileNotFoundError, NotADirectoryError) as exc:
        stderr.write(f"error: {exc}\n")
        return 2

    rendered = (
        json.dumps(manifest.to_dict(), indent=2, sort_keys=True)
        if args.format == "json"
        else render_text_manifest(manifest)
    )

    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    else:
        stdout.write(rendered + "\n")

    return 0


def render_text_manifest(manifest: RepositoryManifest) -> str:
    lines = [
        "OpenHarness RepoAgent Manifest",
        "",
        f"Repository: {manifest.repository.root}",
        f"Branch: {manifest.repository.current_branch or 'unknown'}",
        f"Commit: {manifest.repository.commit_sha or 'unknown'}",
        f"Files: {manifest.total_files}",
        f"Bytes: {manifest.total_bytes}",
        "",
        "Languages:",
    ]

    lines.extend(
        f"- {language.name}: {language.files} files, {language.bytes} bytes"
        for language in manifest.languages
    )
    if not manifest.languages:
        lines.append("- none detected")

    lines.append("")
    lines.append("Frameworks:")
    lines.extend(f"- {framework}" for framework in manifest.frameworks)
    if not manifest.frameworks:
        lines.append("- none detected")

    lines.append("")
    lines.append("API Routes:")
    lines.extend(
        f"- {route.method} {route.path} ({route.framework}, {route.source})"
        for route in manifest.api_routes
    )
    if not manifest.api_routes:
        lines.append("- none detected")

    lines.append("")
    lines.append("Infrastructure:")
    lines.extend(f"- {item}" for item in manifest.infrastructure)
    if not manifest.infrastructure:
        lines.append("- none detected")

    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())

