# Technical Design

## 1. Scope

This design covers the initial OpenHarness platform and PerfAgent MVP.

Production implementation should begin only after this document and the architecture package are approved.

## 2. Technology Baseline

Backend:

- Python 3.10+
- FastAPI
- Pydantic v2
- LangGraph
- SQLAlchemy or SQLModel
- PostgreSQL
- pgvector
- Redis

Execution and delivery:

- Docker and Docker Compose for local mode
- k6 for performance test execution
- GitHub integration first
- Harness integration after PerfAgent MVP proves the workflow

Observability:

- OpenTelemetry traces
- Structured JSON logs
- Prometheus-compatible metrics

Testing:

- Pytest
- Integration tests with Docker Compose
- Golden-file tests for reports and generated k6 scripts
- End-to-end tests against example repositories

## 3. Domain Model

### Repository

Represents a source repository known to OpenHarness.

Important fields:

- `id`
- `provider`
- `remote_url`
- `default_branch`
- `local_path`
- `metadata`

### Repository Snapshot

Represents one analyzed version of a repository.

Important fields:

- `id`
- `repository_id`
- `commit_sha`
- `detected_languages`
- `detected_frameworks`
- `service_map`
- `dependency_map`
- `api_inventory`
- `test_inventory`
- `created_at`

### Workflow Run

Represents one execution of an agent workflow.

Important fields:

- `id`
- `agent_name`
- `workflow_name`
- `status`
- `trigger`
- `repository_id`
- `commit_sha`
- `started_at`
- `finished_at`
- `failure_reason`

### Workflow Event

Append-only event emitted during workflow execution.

Important fields:

- `id`
- `workflow_run_id`
- `step_name`
- `event_type`
- `payload`
- `created_at`

### Artifact

Generated file or structured output from a workflow.

Important fields:

- `id`
- `workflow_run_id`
- `artifact_type`
- `path`
- `content_hash`
- `metadata`

## 4. Runtime Design

The runtime executes workflows as explicit graphs.

Core interfaces:

- `Agent`: declares name, capabilities, workflows, and tool requirements.
- `Workflow`: declares graph nodes, input schema, output schema, and policies.
- `WorkflowContext`: carries run id, repository snapshot, memory access, tool registry, artifact store, logger, and approval state.
- `Tool`: exposes typed input and output schemas.
- `Policy`: validates whether an action is allowed.
- `ArtifactStore`: persists generated outputs.

Runtime lifecycle:

1. Receive workflow request.
2. Validate input schema and policy.
3. Create workflow run.
4. Resolve tools and memory.
5. Execute graph nodes.
6. Persist events and artifacts.
7. Emit final report or failure summary.

## 5. Tool Contract Design

Tools should use typed contracts.

Each tool declares:

- Name
- Version
- Description
- Input schema
- Output schema
- Required permissions
- Side-effect level
- Timeout
- Retry policy

Side-effect levels:

- `read_only`: repository inspection, metrics reads, local file reads
- `local_write`: generated local artifacts
- `external_write`: PR comments, remote branches, pipeline updates
- `deployment`: production or production-like operational changes

`external_write` and `deployment` actions require explicit policy checks and may require human approval.

## 6. RepoAgent Design

RepoAgent produces repository intelligence for other agents.

Pipeline:

1. Discover files and ignore generated/vendor paths.
2. Detect languages and package managers.
3. Detect frameworks and service entrypoints.
4. Extract API routes where supported.
5. Detect databases, queues, caches, and external services.
6. Detect existing tests and benchmark assets.
7. Build a repository manifest and service map.
8. Persist a repository snapshot.

Initial analyzer support:

- Python FastAPI and Flask
- Node.js Express and Next.js API routes
- Java Spring Boot
- Dockerfile and Docker Compose
- Kubernetes manifests

The first MVP can support a smaller subset, but the interfaces should anticipate this roadmap.

## 7. PerfAgent Design

PerfAgent depends on RepoAgent output.

Workflow nodes:

1. `load_repository_snapshot`
2. `identify_performance_targets`
3. `create_test_plan`
4. `generate_k6_scripts`
5. `validate_k6_scripts`
6. `execute_k6`
7. `collect_metrics`
8. `analyze_results`
9. `render_report`
10. `publish_comment` for GitHub mode only

### Performance Target Identification

PerfAgent ranks candidate targets using:

- Public HTTP routes
- Write-heavy endpoints
- Search/list endpoints
- Authentication and checkout-like flows
- Existing API documentation
- Historical performance issues where available

### Test Plan

The test plan should be human-readable and machine-executable.

It should include:

- Target endpoint or flow
- Scenario purpose
- Load profile
- Thresholds
- Test data needs
- Assumptions
- Safety notes

### k6 Generation

Generated k6 scripts should:

- Be deterministic for the same plan input where possible
- Include thresholds
- Separate configuration from scenario logic
- Avoid embedding secrets
- Be saved as artifacts
- Include comments only where they clarify generated assumptions

### Metrics Analysis

Initial metrics:

- Request rate
- Latency percentiles: p50, p90, p95, p99
- Error rate
- HTTP status distribution
- Throughput
- k6 threshold pass/fail

Report output:

- Executive summary
- Tested scenarios
- Key metrics table
- Risks and suspected bottlenecks
- Reproduction command
- Recommended next actions

## 8. API Design

Initial API routes:

- `POST /v1/repositories/analyze`
- `GET /v1/repositories/{repository_id}/snapshots/{snapshot_id}`
- `POST /v1/agents/perf/plan`
- `POST /v1/agents/perf/run`
- `GET /v1/workflow-runs/{run_id}`
- `GET /v1/workflow-runs/{run_id}/events`
- `GET /v1/workflow-runs/{run_id}/artifacts`

The API should be useful for both UI and automation clients.

## 9. CLI Design

Initial CLI commands:

```text
openharness analyze --repo .
openharness perf plan --repo .
openharness perf run --repo . --plan openharness/perf-plan.yaml
openharness perf report --run <run-id>
```

The CLI should be the fastest path to the first successful user experience.

## 10. Persistence Design

PostgreSQL stores:

- Repositories
- Repository snapshots
- Workflow runs
- Workflow events
- Artifacts metadata
- Integration installations

pgvector stores:

- Repository summaries
- Code and documentation embeddings
- Prior run summaries

Redis stores:

- Short-lived workflow coordination state
- Optional queue state for local workers

Artifact files may start on local disk for MVP and move to S3-compatible object storage later.

## 11. Security Design

Required controls for MVP:

- Redact secrets from logs and generated reports.
- Block generated tests from using production URLs unless explicitly allowed.
- Require approval before posting PR comments.
- Treat remote repository writes as external side effects.
- Store integration tokens as secrets, not plaintext configuration.
- Keep generated artifacts scoped to workflow runs.

## 12. Testing Strategy

Unit tests:

- Runtime state transitions
- Tool schema validation
- RepoAgent detectors
- PerfAgent planning logic
- k6 output parser
- Report renderer

Integration tests:

- Analyze fixture repositories
- Generate and validate k6 scripts
- Execute a small local service under k6
- Persist workflow events and artifacts

End-to-end tests:

- Run PerfAgent against example repositories
- Produce a stable Markdown report
- Optionally simulate a GitHub PR comment without writing to GitHub

## 13. Open Questions

- Which license should the project use: Apache-2.0 or MIT?
- Should the first runtime expose MCP tools internally, externally, or both?
- Should local mode require PostgreSQL on day one, or start with SQLite plus a migration path?
- How much of LangGraph should be exposed in public extension APIs?
- Should generated k6 scripts be committed back to repositories or remain run artifacts by default?
