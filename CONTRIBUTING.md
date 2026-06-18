# Contributing to OpenHarness AI

Thank you for helping build OpenHarness AI.

The project is early, so the best contributions are small, testable improvements that make the first developer workflow clearer and more reliable.

## Development Setup

```bash
python3.10 -m pip install -e ".[dev]"
openharness analyze --repo . --format text
pytest
```

## Contribution Guidelines

- Keep changes focused.
- Add tests for behavior changes.
- Update documentation when user-facing behavior changes.
- Avoid external side effects in tests.
- Do not add production integrations that write to external systems without an approval gate.

## Good First Contributions

- Add framework detectors to RepoAgent.
- Improve route extraction for supported frameworks.
- Add example repositories.
- Improve CLI output.
- Add documentation screenshots or example manifests.

## Pull Request Checklist

- Tests pass locally.
- New behavior is documented.
- Generated files and secrets are not committed.
- The PR explains the user-visible value.
