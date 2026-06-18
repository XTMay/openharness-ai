from __future__ import annotations

import json
from pathlib import Path

from openharness.agents.repo_agent import analyze_repository


def test_repo_agent_detects_fastapi_routes(tmp_path):
    app_file = tmp_path / "app.py"
    app_file.write_text(
        "\n".join(
            [
                "from fastapi import FastAPI",
                "app = FastAPI()",
                "",
                '@app.get("/health")',
                "def health():",
                "    return {'ok': True}",
                "",
                '@app.post("/orders")',
                "def create_order():",
                "    return {'id': 1}",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")

    manifest = analyze_repository(tmp_path)

    assert [language.name for language in manifest.languages] == ["Python"]
    assert [framework.name for framework in manifest.frameworks] == ["FastAPI"]
    assert manifest.frameworks[0].confidence == "high"
    assert manifest.frameworks[0].evidence[0].source == "app.py"
    assert "Python project" in manifest.package_managers
    assert {(route.method, route.path) for route in manifest.api_routes} == {
        ("GET", "/health"),
        ("POST", "/orders"),
    }
    assert manifest.api_routes[0].evidence[0].line == 4
    fastapi_targets = [
        (target.method, target.path, target.priority) for target in manifest.performance_targets
    ]
    assert fastapi_targets == [
        ("POST", "/orders", "high")
    ]
    assert manifest.service_entrypoints[0].kind == "python_app"


def test_repo_agent_detects_express_and_node_scripts(tmp_path):
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "scripts": {"start": "node server.js", "test": "node --test"},
                "dependencies": {"express": "^4.18.0"},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "server.js").write_text(
        "\n".join(
            [
                "const express = require('express');",
                "const app = express();",
                "app.get('/products', (req, res) => res.json([]));",
                "app.post('/checkout', (req, res) => res.json({ok: true}));",
            ]
        ),
        encoding="utf-8",
    )

    manifest = analyze_repository(tmp_path)

    assert "JavaScript" in [language.name for language in manifest.languages]
    assert [framework.name for framework in manifest.frameworks] == ["Express"]
    assert manifest.frameworks[0].confidence == "high"
    assert "npm" in manifest.package_managers
    assert "package.json#scripts.test" in manifest.test_inventory
    assert {(route.method, route.path) for route in manifest.api_routes} == {
        ("GET", "/products"),
        ("POST", "/checkout"),
    }
    express_targets = [
        (target.method, target.path, target.priority) for target in manifest.performance_targets
    ]
    assert express_targets == [
        ("POST", "/checkout", "high"),
        ("GET", "/products", "medium"),
    ]
    assert any(entrypoint.kind == "node_script" for entrypoint in manifest.service_entrypoints)


def test_repo_agent_ignores_common_vendor_directories(tmp_path):
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "ignored.js").write_text("app.get('/ignored')", encoding="utf-8")
    (tmp_path / "main.py").write_text("print('hello')", encoding="utf-8")

    manifest = analyze_repository(tmp_path)

    assert manifest.total_files == 1
    assert not manifest.api_routes


def test_repo_agent_does_not_treat_test_fixtures_as_service_routes(tmp_path):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_routes.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/fixture')\ndef fixture(): pass\n",
        encoding="utf-8",
    )

    manifest = analyze_repository(tmp_path)

    assert "tests/test_routes.py" in manifest.test_inventory
    assert "FastAPI" not in [framework.name for framework in manifest.frameworks]
    assert not manifest.api_routes
    assert not manifest.service_entrypoints


def test_repo_agent_analyzes_fastapi_example():
    repo_root = Path(__file__).resolve().parents[3]
    example_path = repo_root / "examples" / "fastapi-service"

    manifest = analyze_repository(example_path)

    assert [framework.name for framework in manifest.frameworks] == ["FastAPI"]
    assert {(route.method, route.path) for route in manifest.api_routes} == {
        ("GET", "/health"),
        ("GET", "/products"),
        ("POST", "/orders"),
        ("POST", "/checkout"),
    }
    example_targets = [
        (target.method, target.path, target.priority) for target in manifest.performance_targets
    ]
    assert example_targets == [
        ("POST", "/checkout", "high"),
        ("POST", "/orders", "high"),
        ("GET", "/products", "medium"),
    ]
