# Security Policy

OpenHarness AI is an early-stage open-source project.

## Supported Versions

Security fixes currently target the main branch until the first stable release.

## Reporting a Vulnerability

Please do not open a public issue for a suspected vulnerability.

Until a dedicated security contact is configured, use a private GitHub security advisory for the repository after it is published.

## Security Principles

- Agents must treat external writes as governed actions.
- Secrets must not be logged, embedded into prompts, or included in reports.
- Generated performance tests must not target production systems by default.
- Tool permissions should be explicit and scoped.
- Workflow events should support auditability without exposing sensitive data.

