# OpenHarness AI

OpenHarness AI is an open-source AI-native software delivery platform.

Its mission is to provide the AI layer that turns CI/CD platforms into engineering systems that can understand repositories, plan workflows, run delivery tools, and explain results through autonomous agents.

The first flagship application is **PerfAgent**, an AI performance engineering agent that analyzes a repository, plans performance tests, generates k6 scripts, runs tests, analyzes metrics, and reports performance risk back to developers.

## Current Status

This repository has entered initial development.

The first implemented tool is RepoAgent Analyze, a read-only repository intelligence CLI.

```bash
openharness analyze --repo .
```

## Design Package

- [Architecture Document](docs/architecture.md)
- [Repository Structure](docs/repository-structure.md)
- [Technical Design](docs/technical-design.md)
- [MVP Roadmap](docs/mvp-roadmap.md)
- [Development Plan](docs/development-plan.md)

## Local Development

```bash
python3.12 -m pip install -e ".[dev]"
openharness analyze --repo . --format text
pytest
```

## Project Principles

- Build a long-term open-source platform, not a disposable demo.
- Keep the core runtime small and extensible.
- Treat agents as workflow participants with explicit inputs, outputs, tools, and audit trails.
- Make every autonomous action observable, replayable, and governable.
- Start with PerfAgent as the killer application, then grow into an ecosystem of delivery agents.
