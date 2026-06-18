# Repository Structure

## 1. Target Layout

```text
openharness-ai/
  README.md
  LICENSE
  CONTRIBUTING.md
  CODE_OF_CONDUCT.md
  SECURITY.md
  pyproject.toml
  docker-compose.yml
  .env.example
  .github/
    workflows/
      ci.yml
  docs/
    architecture.md
    repository-structure.md
    technical-design.md
    mvp-roadmap.md
    adr/
  backend/
    openharness/
      api/
      runtime/
      workflows/
      memory/
      tools/
      integrations/
      agents/
        repo_agent/
        perf_agent/
        review_agent/
        security_agent/
        deploy_agent/
        incident_agent/
      observability/
      governance/
      config/
    tests/
      unit/
      integration/
      e2e/
  cli/
    openharness_cli/
    tests/
  examples/
    perf-agent/
      fastapi-service/
      node-api/
      spring-service/
  deployments/
    docker/
    helm/
    kubernetes/
  scripts/
  tools/
    dev/
    evaluation/
```

## 2. Directory Responsibilities

### `backend/openharness/api`

FastAPI application, request models, response models, webhook handlers, and service-level dependency injection.

### `backend/openharness/runtime`

Core agent runtime abstractions:

- Workflow run lifecycle
- State graph execution
- Step events
- Retry policy
- Artifact handling
- Runtime errors

### `backend/openharness/workflows`

Reusable workflow definitions and graph composition helpers.

Domain agents may own specific workflows, but shared orchestration patterns belong here.

### `backend/openharness/memory`

Repository memory, vector retrieval, workflow history, and durable context APIs.

This package should hide database and vector-store implementation details from agents.

### `backend/openharness/tools`

Typed tool contracts and built-in tool implementations.

Tool modules should expose explicit input/output schemas and avoid reaching directly into agent internals.

### `backend/openharness/integrations`

External product integrations:

- GitHub
- GitLab
- Harness
- Prometheus
- OpenTelemetry collectors
- k6 execution adapters

### `backend/openharness/agents`

Agent packages. Each agent should include:

- Workflow graph definitions
- Planner and analyzer modules
- Prompt templates
- Tool requirements
- Policies
- Tests
- Agent-specific documentation

### `backend/openharness/observability`

Logging, metrics, tracing, event export, and run diagnostics.

### `backend/openharness/governance`

Policy checks, approval gates, permission scopes, and external side-effect controls.

### `cli`

Command-line interface for local developer workflows.

Initial commands should focus on:

- `openharness analyze`
- `openharness perf plan`
- `openharness perf run`
- `openharness perf report`

### `examples`

Runnable example repositories and sample configuration.

Examples are part of the product. They must stay tested.

### `deployments`

Docker, Helm, and Kubernetes deployment assets.

Production-oriented deployment assets should not block the local-first MVP.

### `docs/adr`

Architecture Decision Records.

Use ADRs for decisions that affect long-term architecture, extension contracts, security boundaries, or storage choices.

## 3. Package Boundary Rules

- Agents may depend on runtime, memory, tools, integrations, observability, and governance.
- Runtime must not depend on a specific agent.
- Tools must not depend on a specific agent.
- Integrations must not depend on a specific workflow.
- API and CLI call into application services, not directly into low-level tool implementations.
- Tests should mirror package boundaries.

## 4. Initial Repository Milestones

1. Add open-source project files: license, contributing guide, code of conduct, security policy.
2. Add Python project scaffolding and CI.
3. Add runtime and tool contract interfaces.
4. Add RepoAgent analysis skeleton.
5. Add PerfAgent MVP workflow.
6. Add local Docker Compose developer path.

