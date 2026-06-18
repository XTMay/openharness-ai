# OpenHarness AI Architecture

## 1. Vision

OpenHarness AI is an AI engineering operating system for software delivery.

It provides a runtime and ecosystem for autonomous engineering agents that can understand source code, infrastructure, CI/CD workflows, runtime telemetry, and business context.

The long-term goal is to make AI-native delivery workflows composable across code review, performance engineering, security validation, deployment, and incident response.

## 2. Architectural Goals

- Provide a stable agent runtime that can execute long-running engineering workflows.
- Separate platform capabilities from domain-specific agents.
- Support both local developer usage and CI/CD execution.
- Make agent decisions auditable through events, traces, artifacts, and reports.
- Keep integrations modular so GitHub, GitLab, Harness, k6, Semgrep, Trivy, Prometheus, and future tools can evolve independently.
- Avoid a monolith by building a platform core plus focused agents.

## 3. System Context

```text
Developer / Platform Engineer / SRE
        |
        v
OpenHarness API / CLI / CI Integration
        |
        v
Agent Runtime + Workflow Engine
        |
        +--> Repository Intelligence
        +--> Tool Integration Layer
        +--> Memory and Knowledge Store
        +--> Agent Ecosystem
        |
        v
External Systems: GitHub, GitLab, Harness, k6, Kubernetes, Prometheus, Grafana, OpenTelemetry
```

## 4. Core Components

### 4.1 Agent Runtime

The Agent Runtime executes autonomous workflows.

Responsibilities:

- Accept workflow requests from API, CLI, CI jobs, or webhooks.
- Manage planning, execution, retries, reflection, and termination.
- Coordinate tool calls through typed tool contracts.
- Persist workflow events and agent state.
- Emit traces, metrics, logs, and artifacts.

Initial technology choices:

- Python 3.12
- LangGraph for stateful agent workflows
- MCP-compatible tool boundaries where useful
- FastAPI for service APIs
- Redis for short-lived execution coordination
- PostgreSQL for durable metadata
- pgvector for semantic memory and retrieval

### 4.2 Workflow Engine

The Workflow Engine provides deterministic structure around agent behavior.

Responsibilities:

- Define workflow graphs with explicit nodes and transitions.
- Enforce guardrails before external side effects.
- Track step inputs, outputs, timing, and status.
- Resume interrupted workflows where possible.
- Support human approval gates for risky actions.

Agent reasoning can be probabilistic. Workflow control should remain explicit.

### 4.3 Repository Intelligence Engine

RepoAgent builds repository understanding used by other agents.

Responsibilities:

- Detect languages, frameworks, package managers, services, APIs, databases, deployment assets, and test surfaces.
- Extract repository facts into a structured knowledge graph.
- Produce summaries optimized for downstream agents.
- Maintain incremental analysis as a repository changes.

Initial output:

- Repository manifest
- Service map
- Dependency map
- API and route inventory
- Test surface inventory
- Performance entrypoint candidates

### 4.4 Tool Integration Layer

Tools are external capabilities exposed to agents through typed interfaces.

Initial tool families:

- Source control: clone, diff, branch metadata, PR metadata
- Test generation: k6 script creation and validation
- Execution: local process execution, Docker execution, CI execution
- Observability: metrics and traces from k6, Prometheus, OpenTelemetry
- Reporting: Markdown reports, PR comments, JSON artifacts
- Enterprise delivery: Harness connector and pipeline generation

### 4.5 Memory System

The Memory System stores durable engineering context.

Memory types:

- Repository memory: stable facts about a repository
- Workflow memory: prior runs, decisions, and outcomes
- Organization memory: reusable policies, SLOs, standards, and templates
- Agent memory: tool performance, prompt versions, and evaluation history

Memory must be scoped and permissioned. Organization memory must not leak across tenants.

### 4.6 Agent Ecosystem

The core platform should support focused agents:

- RepoAgent: repository intelligence
- PerfAgent: performance engineering
- ReviewAgent: code and architecture review
- SecurityAgent: security validation
- DeployAgent: deployment planning and validation
- IncidentAgent: incident analysis and remediation suggestions

Each agent should be packaged as a module with workflow definitions, tool requirements, prompts, policies, tests, and documentation.

## 5. First Flagship: PerfAgent

PerfAgent is the first end-to-end proof of the platform.

Primary workflow:

```text
Git Repository
  -> RepoAgent repository analysis
  -> Performance Planner
  -> k6 Script Generator
  -> k6 Executor
  -> Metrics Collector
  -> AI Performance Analyst
  -> Report and PR Comment
```

MVP scope:

- Analyze a repository and identify likely performance-sensitive entrypoints.
- Generate a reviewable k6 test plan.
- Generate k6 scripts from approved plans or safe defaults.
- Execute tests locally or in Docker.
- Parse k6 JSON output.
- Produce a Markdown report with risks, bottlenecks, and next actions.

## 6. Deployment Model

OpenHarness should support three deployment modes:

- Local developer mode: `git clone`, `docker compose up`, run first agent.
- CI mode: run agents inside GitHub Actions, GitLab CI, or Harness pipelines.
- Platform mode: long-running API service with database, queue, workers, and integrations.

The MVP should optimize for local developer mode while preserving clean seams for CI and platform mode.

## 7. Security and Governance

Autonomous engineering agents must have explicit boundaries.

Required controls:

- Tool allowlists by workflow.
- Human approval gates before irreversible external side effects.
- Secret redaction in logs, prompts, reports, and artifacts.
- Tenant and repository isolation.
- Full event audit trail.
- Policy checks before PR comments, pipeline changes, remote pushes, or deployment actions.

## 8. Observability

Every workflow run should emit:

- Structured logs
- OpenTelemetry traces
- Runtime metrics
- Step-level events
- Artifacts such as plans, generated scripts, execution outputs, and reports

Debuggability is a product feature. A failed workflow should explain which step failed, why, and what data was used.

## 9. Extension Model

OpenHarness should allow community contributors to add:

- New agents
- New tools
- New workflow templates
- New repository analyzers
- New reporting formats
- New CI/CD integrations

Extension contracts should be versioned and documented before the first external plugin API is declared stable.

## 10. Architectural Decision Checklist

Before production code starts, the project should approve:

- Initial runtime boundaries
- MVP persistence model
- Agent packaging conventions
- Tool contract format
- PerfAgent MVP scope
- Local-first developer experience
- Security approval gates for external side effects

