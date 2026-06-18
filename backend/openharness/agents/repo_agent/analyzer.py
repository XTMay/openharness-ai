"""RepoAgent repository analyzer."""

from __future__ import annotations

import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from openharness.agents.repo_agent.models import (
    ApiRoute,
    LanguageStat,
    RepositoryIdentity,
    RepositoryManifest,
    ServiceEntrypoint,
)
from openharness.agents.repo_agent.scanner import FileRecord, scan_repository

EXTENSION_LANGUAGES = {
    ".go": "Go",
    ".java": "Java",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".kt": "Kotlin",
    ".py": "Python",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
}

TEXT_EXTENSIONS = {
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".json",
    ".kt",
    ".py",
    ".rb",
    ".rs",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}

FASTAPI_ROUTE_PATTERN = re.compile(
    r"@(?:app|router)\.(get|post|put|delete|patch|options|head)\(\s*[\"']([^\"']+)",
    re.IGNORECASE,
)
FLASK_ROUTE_PATTERN = re.compile(r"@app\.route\(\s*[\"']([^\"']+)", re.IGNORECASE)
EXPRESS_ROUTE_PATTERN = re.compile(
    r"(?:app|router)\.(get|post|put|delete|patch|options|head)\(\s*[\"']([^\"']+)",
    re.IGNORECASE,
)
SPRING_ROUTE_PATTERN = re.compile(
    r"@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)"
    r"\(\s*(?:value\s*=\s*)?[\"']([^\"']+)",
    re.IGNORECASE,
)


def analyze_repository(repo_path: str | Path, max_files: int = 10_000) -> RepositoryManifest:
    root = Path(repo_path).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Repository path does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Repository path is not a directory: {root}")

    scan = scan_repository(root, max_files=max_files)
    text_cache = _read_text_files(scan.files)

    languages = _detect_languages(scan.files)
    package_managers = _detect_package_managers(scan.files)
    frameworks = _detect_frameworks(scan.files, text_cache)
    api_routes = _extract_api_routes(text_cache)
    service_entrypoints = _detect_service_entrypoints(scan.files, text_cache)
    infrastructure = _detect_infrastructure(scan.files, text_cache)
    test_inventory = _detect_tests(scan.files, text_cache)
    warnings: list[str] = []

    if scan.reached_file_limit:
        warnings.append(f"Repository scan reached max file limit: {max_files}")

    return RepositoryManifest(
        repository=RepositoryIdentity(
            root=root.as_posix(),
            current_branch=_git_output(root, "rev-parse", "--abbrev-ref", "HEAD"),
            commit_sha=_git_output(root, "rev-parse", "HEAD"),
        ),
        generated_at=datetime.now(timezone.utc).isoformat(),
        total_files=len(scan.files),
        total_bytes=sum(file.size for file in scan.files),
        languages=languages,
        package_managers=package_managers,
        frameworks=frameworks,
        service_entrypoints=service_entrypoints,
        api_routes=api_routes,
        infrastructure=infrastructure,
        test_inventory=test_inventory,
        warnings=warnings,
    )


def _detect_languages(files: Iterable[FileRecord]) -> list[LanguageStat]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for file in files:
        language = EXTENSION_LANGUAGES.get(Path(file.relative_path).suffix.lower())
        if language is None:
            continue
        counts[language]["files"] += 1
        counts[language]["bytes"] += file.size

    return [
        LanguageStat(name=language, files=stats["files"], bytes=stats["bytes"])
        for language, stats in sorted(counts.items(), key=lambda item: (-item[1]["files"], item[0]))
    ]


def _detect_package_managers(files: Iterable[FileRecord]) -> list[str]:
    filenames = {Path(file.relative_path).name for file in files}
    managers = []
    mapping = {
        "pyproject.toml": "Python project",
        "requirements.txt": "pip",
        "poetry.lock": "Poetry",
        "uv.lock": "uv",
        "package.json": "npm",
        "package-lock.json": "npm lockfile",
        "pnpm-lock.yaml": "pnpm",
        "yarn.lock": "Yarn",
        "pom.xml": "Maven",
        "build.gradle": "Gradle",
        "build.gradle.kts": "Gradle",
        "go.mod": "Go modules",
        "Cargo.toml": "Cargo",
    }

    for filename, manager in mapping.items():
        if filename in filenames:
            managers.append(manager)

    return sorted(managers)


def _detect_frameworks(files: Iterable[FileRecord], text_cache: dict[str, str]) -> list[str]:
    frameworks: set[str] = set()
    filenames = {Path(file.relative_path).name for file in files}

    for path, text in text_cache.items():
        if _is_test_path(path):
            continue
        suffix = Path(path).suffix.lower()
        if suffix == ".py":
            if _contains_fastapi_app(text):
                frameworks.add("FastAPI")
            if _contains_flask_app(text):
                frameworks.add("Flask")
        if suffix in {".js", ".jsx", ".ts", ".tsx"}:
            if "express(" in text or "from 'express'" in text or 'from "express"' in text:
                frameworks.add("Express")
            if "next" in text.lower() and "package.json" in filenames:
                frameworks.add("Next.js")
        if suffix in {".java", ".kt"}:
            if "@SpringBootApplication" in text:
                frameworks.add("Spring Boot")

    package_json = text_cache.get("package.json")
    if package_json:
        try:
            package_data = json.loads(package_json)
        except json.JSONDecodeError:
            package_data = {}
        dependencies = {
            **package_data.get("dependencies", {}),
            **package_data.get("devDependencies", {}),
        }
        if "express" in dependencies:
            frameworks.add("Express")
        if "next" in dependencies:
            frameworks.add("Next.js")

    return sorted(frameworks)


def _extract_api_routes(text_cache: dict[str, str]) -> list[ApiRoute]:
    routes: list[ApiRoute] = []

    for path, text in sorted(text_cache.items()):
        if _is_test_path(path):
            continue
        suffix = Path(path).suffix.lower()
        if suffix == ".py":
            for match in FASTAPI_ROUTE_PATTERN.finditer(text):
                routes.append(
                    ApiRoute(
                        method=match.group(1).upper(),
                        path=match.group(2),
                        source=path,
                        framework="FastAPI",
                    )
                )
            for match in FLASK_ROUTE_PATTERN.finditer(text):
                routes.append(
                    ApiRoute(
                        method="ANY",
                        path=match.group(1),
                        source=path,
                        framework="Flask",
                    )
                )
        elif suffix in {".js", ".jsx", ".ts", ".tsx"}:
            for match in EXPRESS_ROUTE_PATTERN.finditer(text):
                routes.append(
                    ApiRoute(
                        method=match.group(1).upper(),
                        path=match.group(2),
                        source=path,
                        framework="Express",
                    )
                )
        elif suffix in {".java", ".kt"}:
            for match in SPRING_ROUTE_PATTERN.finditer(text):
                routes.append(
                    ApiRoute(
                        method=_spring_method(match.group(1)),
                        path=match.group(2),
                        source=path,
                        framework="Spring Boot",
                    )
                )

    return routes


def _detect_service_entrypoints(
    files: Iterable[FileRecord], text_cache: dict[str, str]
) -> list[ServiceEntrypoint]:
    entrypoints: list[ServiceEntrypoint] = []
    filenames = {Path(file.relative_path).name: file.relative_path for file in files}

    if "Dockerfile" in filenames:
        entrypoints.append(ServiceEntrypoint(kind="container", path=filenames["Dockerfile"]))

    package_json = text_cache.get("package.json")
    if package_json:
        try:
            package_data = json.loads(package_json)
        except json.JSONDecodeError:
            package_data = {}
        scripts = package_data.get("scripts", {})
        for script_name in ("start", "dev", "serve"):
            command = scripts.get(script_name)
            if command:
                entrypoints.append(
                    ServiceEntrypoint(
                        kind="node_script",
                        path="package.json",
                        name=script_name,
                        command=command,
                    )
                )

    for path, text in sorted(text_cache.items()):
        if _is_test_path(path):
            continue
        if Path(path).suffix.lower() == ".py" and (
            _contains_fastapi_app(text) or _contains_flask_app(text)
        ):
            entrypoints.append(ServiceEntrypoint(kind="python_app", path=path))
        if Path(path).suffix.lower() in {".java", ".kt"} and "@SpringBootApplication" in text:
            entrypoints.append(ServiceEntrypoint(kind="spring_boot_app", path=path))

    return entrypoints


def _detect_infrastructure(files: Iterable[FileRecord], text_cache: dict[str, str]) -> list[str]:
    infrastructure: set[str] = set()

    for file in files:
        name = Path(file.relative_path).name.lower()
        if name == "dockerfile":
            infrastructure.add("Dockerfile")
        if name in {"docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"}:
            infrastructure.add("Docker Compose")

    for path, text in text_cache.items():
        name = Path(path).name.lower()
        if name.endswith((".yaml", ".yml")) and "apiVersion:" in text and "kind:" in text:
            infrastructure.add("Kubernetes manifests")

    return sorted(infrastructure)


def _detect_tests(files: Iterable[FileRecord], text_cache: dict[str, str]) -> list[str]:
    inventory: set[str] = set()

    for file in files:
        path = Path(file.relative_path)
        name = path.name
        if "test" in path.parts or "tests" in path.parts:
            inventory.add(path.as_posix())
            continue
        if name.startswith("test_") or name.endswith(("_test.py", ".test.js", ".spec.js", ".test.ts", ".spec.ts")):
            inventory.add(path.as_posix())

    package_json = text_cache.get("package.json")
    if package_json:
        try:
            package_data = json.loads(package_json)
        except json.JSONDecodeError:
            package_data = {}
        if package_data.get("scripts", {}).get("test"):
            inventory.add("package.json#scripts.test")

    for candidate in ("pytest.ini", "tox.ini", "noxfile.py", "vitest.config.ts", "jest.config.js"):
        if candidate in text_cache:
            inventory.add(candidate)

    return sorted(inventory)


def _read_text_files(files: Iterable[FileRecord]) -> dict[str, str]:
    text_cache: dict[str, str] = {}

    for file in files:
        relative = file.relative_path
        suffix = Path(relative).suffix.lower()
        name = Path(relative).name
        if suffix not in TEXT_EXTENSIONS and name not in {
            "Dockerfile",
            "go.mod",
            "package.json",
            "pom.xml",
            "pyproject.toml",
            "requirements.txt",
        }:
            continue
        if file.size > 512_000:
            continue

        try:
            text_cache[relative] = file.path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError:
            continue

    return text_cache


def _is_test_path(path: str) -> bool:
    path_obj = Path(path)
    name = path_obj.name
    return (
        "test" in path_obj.parts
        or "tests" in path_obj.parts
        or name.startswith("test_")
        or name.endswith(("_test.py", ".test.js", ".spec.js", ".test.ts", ".spec.ts"))
    )


def _contains_fastapi_app(text: str) -> bool:
    has_import = re.search(r"^\s*(from\s+fastapi\s+import|import\s+fastapi\b)", text, re.MULTILINE)
    return bool(has_import and "FastAPI(" in text)


def _contains_flask_app(text: str) -> bool:
    has_import = re.search(r"^\s*(from\s+flask\s+import|import\s+flask\b)", text, re.MULTILINE)
    return bool(has_import and "Flask(" in text)


def _git_output(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _spring_method(annotation: str) -> str:
    mapping = {
        "GetMapping": "GET",
        "PostMapping": "POST",
        "PutMapping": "PUT",
        "DeleteMapping": "DELETE",
        "PatchMapping": "PATCH",
        "RequestMapping": "ANY",
    }
    return mapping.get(annotation, "ANY")
