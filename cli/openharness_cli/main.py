"""OpenHarness command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TextIO

from openharness import __version__
from openharness.agents.repo_agent import analyze_repository
from openharness.agents.repo_agent.models import DetectionEvidence, RepositoryManifest


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
        choices=("json", "text", "markdown"),
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
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        stderr.write(f"error: {exc}\n")
        return 2

    if args.format == "json":
        rendered = json.dumps(manifest.to_dict(), indent=2, sort_keys=True)
    elif args.format == "markdown":
        rendered = render_markdown_manifest(manifest)
    else:
        rendered = render_text_manifest(manifest)

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
        f"Config: {manifest.configuration.path or 'none'}",
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
    lines.extend(
        f"- {framework.name} ({framework.confidence} confidence)"
        for framework in manifest.frameworks
    )
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
    lines.append("Performance Targets:")
    lines.extend(
        f"- {target.priority.upper()} {target.method} {target.path}: {target.reason}"
        for target in manifest.performance_targets
    )
    if not manifest.performance_targets:
        lines.append("- none detected")

    lines.append("")
    lines.append("Infrastructure:")
    lines.extend(f"- {item}" for item in manifest.infrastructure)
    if not manifest.infrastructure:
        lines.append("- none detected")

    return "\n".join(lines)


def render_markdown_manifest(manifest: RepositoryManifest) -> str:
    lines = [
        "# OpenHarness RepoAgent Report",
        "",
        "## Repository",
        "",
        f"- Root: `{manifest.repository.root}`",
        f"- Config: `{manifest.configuration.path or 'none'}`",
        f"- Branch: `{manifest.repository.current_branch or 'unknown'}`",
        f"- Commit: `{manifest.repository.commit_sha or 'unknown'}`",
        f"- Files: `{manifest.total_files}`",
        f"- Bytes: `{manifest.total_bytes}`",
        "",
        "## Languages",
        "",
    ]

    if manifest.languages:
        lines.extend(
            f"- **{language.name}**: {language.files} files, {language.bytes} bytes"
            for language in manifest.languages
        )
    else:
        lines.append("- None detected")

    lines.extend(["", "## Frameworks", ""])
    if manifest.frameworks:
        for framework in manifest.frameworks:
            lines.append(f"- **{framework.name}** ({framework.confidence} confidence)")
            for evidence in framework.evidence:
                lines.append(f"  - Evidence: `{_format_evidence(evidence)}`")
    else:
        lines.append("- None detected")

    lines.extend(["", "## API Routes", ""])
    if manifest.api_routes:
        lines.append("| Method | Path | Framework | Source | Confidence |")
        lines.append("| --- | --- | --- | --- | --- |")
        for route in manifest.api_routes:
            lines.append(
                f"| `{route.method}` | `{route.path}` | {route.framework} | "
                f"`{route.source}` | {route.confidence} |"
            )
    else:
        lines.append("- None detected")

    lines.extend(["", "## Performance Targets", ""])
    if manifest.performance_targets:
        lines.append("| Priority | Method | Path | Reason |")
        lines.append("| --- | --- | --- | --- |")
        for target in manifest.performance_targets:
            lines.append(
                f"| {target.priority} | `{target.method}` | `{target.path}` | {target.reason} |"
            )
    else:
        lines.append("- None detected")

    lines.extend(["", "## Service Entrypoints", ""])
    if manifest.service_entrypoints:
        for entrypoint in manifest.service_entrypoints:
            name = f" `{entrypoint.name}`" if entrypoint.name else ""
            command = f" - `{entrypoint.command}`" if entrypoint.command else ""
            lines.append(
                f"- **{entrypoint.kind}**{name}: `{entrypoint.path}` "
                f"({entrypoint.confidence} confidence){command}"
            )
    else:
        lines.append("- None detected")

    lines.extend(["", "## Infrastructure", ""])
    if manifest.infrastructure:
        lines.extend(f"- {item}" for item in manifest.infrastructure)
    else:
        lines.append("- None detected")

    lines.extend(["", "## Tests", ""])
    if manifest.test_inventory:
        lines.extend(f"- `{item}`" for item in manifest.test_inventory)
    else:
        lines.append("- None detected")

    if manifest.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in manifest.warnings)

    lines.extend(["", "## Configuration", ""])
    lines.append(f"- Config file: `{manifest.configuration.path or 'none'}`")
    lines.append(
        "- Ignore patterns: "
        + (
            ", ".join(f"`{pattern}`" for pattern in manifest.configuration.ignore)
            if manifest.configuration.ignore
            else "none"
        )
    )
    lines.append(
        "- Service roots: "
        + (
            ", ".join(f"`{path}`" for path in manifest.configuration.service_roots)
            if manifest.configuration.service_roots
            else "none"
        )
    )
    lines.append(
        "- Production paths: "
        + (
            ", ".join(f"`{path}`" for path in manifest.configuration.production_paths)
            if manifest.configuration.production_paths
            else "none"
        )
    )

    return "\n".join(lines)


def _format_evidence(evidence: DetectionEvidence) -> str:
    suffix = f":{evidence.line}" if evidence.line is not None else ""
    return f"{evidence.source}{suffix} - {evidence.detail}"


if __name__ == "__main__":
    raise SystemExit(main())
