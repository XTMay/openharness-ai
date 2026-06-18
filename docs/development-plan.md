# Development Plan

## 1. Product Direction

OpenHarness AI should grow by delivering one useful open-source workflow at a time.

The first public promise should be:

> Run OpenHarness against a repository and get an actionable engineering signal in minutes.

For the first release, that signal is repository intelligence from RepoAgent. PerfAgent will build on top of it.

## 2. Open Source Growth Strategy

The project should earn forks and stars through practical developer value, not marketing-only positioning.

Priorities:

- Make the first run fast: clone, install, analyze a repository.
- Publish clear examples with real output.
- Keep the README outcome-oriented.
- Add small, well-labeled Good First Issues.
- Treat generated reports and manifests as shareable artifacts.
- Use GitHub Actions so contributors trust the project health quickly.
- Keep the roadmap public and honest.

## 3. First Tool: RepoAgent Analyze

RepoAgent Analyze is the foundation tool.

Command:

```text
openharness analyze --repo .
```

Responsibilities:

- Scan a repository safely.
- Ignore common generated and vendor directories.
- Detect languages.
- Detect package managers.
- Detect frameworks.
- Extract basic API routes.
- Attach evidence and confidence to key detections.
- Identify service entrypoints.
- Identify infrastructure files.
- Identify tests.
- Output a structured manifest in JSON, text, or Markdown.
- Produce performance target candidates for PerfAgent.

Why this comes first:

- PerfAgent needs repository context before it can plan performance tests.
- ReviewAgent, SecurityAgent, DeployAgent, and IncidentAgent will also need repository context.
- It creates a useful demo without external credentials or risky side effects.

## 4. Release Path

### Milestone 1: RepoAgent CLI

Status: implemented and improving.

Deliverables:

- Python package scaffold. Done.
- `openharness analyze`. Done.
- JSON, text, and Markdown outputs. Done.
- Evidence and confidence for key detections. Done.
- Performance target candidates. Done.
- `openharness.yaml` repository configuration. Done.
- Manifest JSON Schema. Done.
- FastAPI example repository. Done.
- Unit tests. Done.
- CI. Done.
- Documentation. In progress.

### Milestone 2: PerfAgent Plan

Deliverables:

- Use RepoAgent manifest as input. Done.
- Rank performance-sensitive routes. Done.
- Generate a test plan. Done.
- Save the plan as JSON, text, or Markdown. Done.
- Provide a performance plan JSON Schema. Done.

### Milestone 3: PerfAgent k6 Generation

Deliverables:

- Generate k6 scripts from a test plan. Done.
- Save scripts as reviewable artifacts. Done.
- Include a k6 generation result schema. Done.
- Defer execution to the next milestone.

### Milestone 4: PerfAgent Run and Report

Deliverables:

- Execute k6 locally.
- Parse k6 output.
- Generate Markdown report.

### Milestone 5: GitHub Preview

Deliverables:

- Render PR comment in dry-run mode.
- Add GitHub Actions example.
- Require explicit approval before posting comments.

## 5. GitHub Launch Checklist

- Choose final repository name and description.
- Add license. Done: Apache-2.0.
- Add contributing guide. Done.
- Add code of conduct. Done.
- Add security policy. Done.
- Add issue templates. Done.
- Add README quickstart.
- Add screenshots or example outputs.
- Tag `v0.1.0-alpha`.
- Announce with a concrete demo, not just a vision statement.
