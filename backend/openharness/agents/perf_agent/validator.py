"""Validate generated k6 artifacts without executing load tests."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from openharness.agents.perf_agent.models import K6ValidationResult, ValidationFinding

WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
SUPPORTED_K6_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}


def validate_k6_artifacts(
    artifacts_dir: str | Path,
    with_k6_inspect: bool = False,
    strict: bool = False,
) -> K6ValidationResult:
    root = Path(artifacts_dir).expanduser().resolve()
    findings: list[ValidationFinding] = []

    if not root.exists():
        findings.append(
            _error("artifacts_dir_missing", "Artifacts directory does not exist.", root)
        )
        return _result(root, findings, strict)

    if not root.is_dir():
        findings.append(
            _error("artifacts_dir_not_directory", "Artifacts path is not a directory.", root)
        )
        return _result(root, findings, strict)

    config = _load_config(root, findings)
    scenarios = _scenarios_from_config(config, root, findings)
    expected_scripts = _expected_script_paths(root, scenarios)
    _check_readme(root, findings)
    _check_script_inventory(root, expected_scripts, findings)
    _check_scenarios(root, scenarios, findings)
    _check_k6_binary(root, expected_scripts, findings, with_k6_inspect)

    return _result(root, findings, strict)


def _load_config(root: Path, findings: list[ValidationFinding]) -> dict[str, Any] | None:
    config_path = root / "config.json"
    if not config_path.exists():
        findings.append(_error("config_json_missing", "config.json is missing.", config_path))
        return None

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        findings.append(
            _error("config_json_invalid", f"config.json is invalid JSON: {exc}", config_path)
        )
        return None

    if not isinstance(config, dict):
        findings.append(
            _error("config_json_not_object", "config.json must contain an object.", config_path)
        )
        return None

    if not isinstance(config.get("scenarios"), list):
        findings.append(
            _error("config_scenarios_missing", "config.json must contain scenarios[].", config_path)
        )

    if not isinstance(config.get("base_url_env"), str):
        findings.append(
            _error(
                "config_base_url_env_missing",
                "config.json must define base_url_env.",
                config_path,
            )
        )

    return config


def _scenarios_from_config(
    config: dict[str, Any] | None, root: Path, findings: list[ValidationFinding]
) -> list[dict[str, Any]]:
    if not config or not isinstance(config.get("scenarios"), list):
        return []

    scenarios: list[dict[str, Any]] = []
    seen_scripts: set[str] = set()

    for index, raw_scenario in enumerate(config["scenarios"]):
        if not isinstance(raw_scenario, dict):
            findings.append(
                _error(
                    "scenario_not_object",
                    f"Scenario at index {index} is not an object.",
                    root / "config.json",
                )
            )
            continue

        scenario = dict(raw_scenario)
        name = scenario.get("name")
        method = scenario.get("method")
        path = scenario.get("path")
        script = scenario.get("script") or (f"{name}.js" if isinstance(name, str) else None)
        scenario_key = scenario.get("scenario_key") or name
        scenario["script"] = script
        scenario["scenario_key"] = scenario_key
        scenarios.append(scenario)

        if not isinstance(name, str) or not name:
            findings.append(
                _error("scenario_name_missing", "Scenario is missing name.", root / "config.json")
            )
        if not isinstance(method, str) or method.upper() not in SUPPORTED_K6_METHODS:
            findings.append(
                _error(
                    "scenario_method_unsupported",
                    f"Scenario {name or index} has unsupported method {method!r}.",
                    root / "config.json",
                )
            )
        if not isinstance(path, str) or not path.startswith("/"):
            findings.append(
                _error(
                    "scenario_path_invalid",
                    f"Scenario {name or index} path must start with '/'.",
                    root / "config.json",
                )
            )
        if isinstance(path, str) and _has_dynamic_path_placeholder(path):
            findings.append(
                _warning(
                    "scenario_dynamic_path",
                    f"Scenario {name or index} uses dynamic path {path}; "
                    "generated scripts need test data.",
                    root / "config.json",
                )
            )
        if isinstance(script, str):
            if script in seen_scripts:
                findings.append(
                    _error(
                        "scenario_script_duplicate",
                        f"Duplicate script name {script}.",
                        root / "config.json",
                    )
                )
            seen_scripts.add(script)
        if isinstance(scenario_key, str) and not _is_valid_js_identifier(scenario_key):
            findings.append(
                _error(
                    "scenario_key_invalid",
                    f"Scenario key {scenario_key!r} is not a valid JavaScript identifier.",
                    root / "config.json",
                )
            )

    return scenarios


def _expected_script_paths(root: Path, scenarios: list[dict[str, Any]]) -> list[Path]:
    paths = []
    for scenario in scenarios:
        script = scenario.get("script")
        if isinstance(script, str):
            paths.append(root / script)
    return paths


def _check_readme(root: Path, findings: list[ValidationFinding]) -> None:
    readme_path = root / "README.md"
    if not readme_path.exists():
        findings.append(
            _warning("readme_missing", "README.md is missing from artifacts.", readme_path)
        )


def _check_script_inventory(
    root: Path, expected_scripts: list[Path], findings: list[ValidationFinding]
) -> None:
    actual_scripts = sorted(root.glob("*.js"))
    expected_set = {path.resolve() for path in expected_scripts}

    if not actual_scripts:
        findings.append(_error("k6_scripts_missing", "No k6 .js scripts found.", root))

    for script_path in expected_scripts:
        if not script_path.exists():
            findings.append(
                _error("k6_script_declared_missing", "Configured script is missing.", script_path)
            )

    for script_path in actual_scripts:
        if script_path.resolve() not in expected_set:
            findings.append(
                _warning("k6_script_unreferenced", "Unreferenced .js script found.", script_path)
            )


def _check_scenarios(
    root: Path, scenarios: list[dict[str, Any]], findings: list[ValidationFinding]
) -> None:
    for scenario in scenarios:
        script = scenario.get("script")
        if not isinstance(script, str):
            continue
        script_path = root / script
        if not script_path.exists():
            continue

        try:
            content = script_path.read_text(encoding="utf-8")
        except OSError as exc:
            findings.append(
                _error("script_unreadable", f"Could not read script: {exc}", script_path)
            )
            continue

        _check_script_shape(content, script_path, findings)
        _check_script_consistency(content, script_path, scenario, findings)


def _check_script_shape(content: str, script_path: Path, findings: list[ValidationFinding]) -> None:
    required_snippets = {
        "script_base_url_missing": "BASE_URL",
        "script_k6_http_import_missing": "k6/http",
        "script_options_missing": "export const options",
        "script_thresholds_missing": "thresholds",
        "script_default_function_missing": "export default function",
        "script_check_missing": "check(response",
    }

    for finding_id, snippet in required_snippets.items():
        if snippet not in content:
            findings.append(
                _error(finding_id, f"Script missing required snippet: {snippet}.", script_path)
            )


def _check_script_consistency(
    content: str,
    script_path: Path,
    scenario: dict[str, Any],
    findings: list[ValidationFinding],
) -> None:
    name = scenario.get("name")
    method = scenario.get("method")
    path = scenario.get("path")
    scenario_key = scenario.get("scenario_key")

    if isinstance(scenario_key, str) and f"{scenario_key}: {{" not in content:
        findings.append(
            _error(
                "script_scenario_key_mismatch",
                f"Script does not contain scenario key {scenario_key!r}.",
                script_path,
            )
        )

    if isinstance(method, str) and method.upper() in SUPPORTED_K6_METHODS:
        expected_method = method.lower()
        if f"http.{expected_method}(" not in content:
            findings.append(
                _error(
                    "script_method_mismatch",
                    f"Script does not use expected k6 HTTP method {expected_method}.",
                    script_path,
                )
            )

    if isinstance(path, str) and f"${{BASE_URL}}{path}" not in content:
        findings.append(
            _error(
                "script_path_mismatch",
                f"Script does not request configured path {path}.",
                script_path,
            )
        )

    if isinstance(method, str) and method.upper() in WRITE_METHODS:
        findings.append(
            _warning(
                "script_placeholder_payload",
                f"Write scenario {name or script_path.name} uses generated placeholder payload.",
                script_path,
            )
        )


def _check_k6_binary(
    root: Path,
    script_paths: list[Path],
    findings: list[ValidationFinding],
    with_k6_inspect: bool,
) -> None:
    k6_path = shutil.which("k6")
    if not k6_path:
        findings.append(
            _warning(
                "k6_binary_missing",
                "k6 not found. Install k6 before running generated scripts.",
                root,
            )
        )
        return

    findings.append(_info("k6_binary_found", f"k6 found at {k6_path}.", root))

    if not with_k6_inspect:
        return

    for script_path in script_paths:
        if script_path.exists():
            _inspect_script(script_path, k6_path, findings)


def _inspect_script(script_path: Path, k6_path: str, findings: list[ValidationFinding]) -> None:
    try:
        result = subprocess.run(
            [k6_path, "inspect", "--execution-requirements", script_path.as_posix()],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        findings.append(
            _error("k6_inspect_failed", f"k6 inspect failed to start: {exc}", script_path)
        )
        return

    if result.returncode == 0:
        findings.append(
            _info("k6_inspect_passed", "k6 inspect completed successfully.", script_path)
        )
    else:
        findings.append(
            _error(
                "k6_inspect_failed",
                (result.stderr or result.stdout or "k6 inspect failed.").strip(),
                script_path,
            )
        )


def _result(root: Path, findings: list[ValidationFinding], strict: bool) -> K6ValidationResult:
    error_count = sum(1 for finding in findings if finding.severity == "error")
    warning_count = sum(1 for finding in findings if finding.severity == "warning")
    valid = error_count == 0 and (warning_count == 0 or not strict)
    summary = f"{error_count} error(s), {warning_count} warning(s)"
    return K6ValidationResult(
        artifacts_dir=root.as_posix(),
        valid=valid,
        summary=summary,
        findings=findings,
    )


def _has_dynamic_path_placeholder(path: str) -> bool:
    return bool(re.search(r"(\{[^}/]+\}|:[A-Za-z_][A-Za-z0-9_]*)", path))


def _is_valid_js_identifier(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", value))


def _error(finding_id: str, message: str, path: Path) -> ValidationFinding:
    return ValidationFinding("error", finding_id, message, path.as_posix())


def _warning(finding_id: str, message: str, path: Path) -> ValidationFinding:
    return ValidationFinding("warning", finding_id, message, path.as_posix())


def _info(finding_id: str, message: str, path: Path) -> ValidationFinding:
    return ValidationFinding("info", finding_id, message, path.as_posix())
