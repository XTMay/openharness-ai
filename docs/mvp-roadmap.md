# MVP Roadmap

## 1. MVP Definition

The MVP proves that OpenHarness can run one valuable AI-native software delivery workflow end to end.

MVP outcome:

A developer can clone OpenHarness, start the local stack, point PerfAgent at an example API repository, generate a performance test plan, run k6, and receive a useful performance report within 10 minutes.

## 2. Non-Goals

The MVP will not include:

- Full multi-tenant SaaS operations
- Production deployment automation
- Complete GitHub App marketplace flow
- Full Harness pipeline generation
- Advanced incident analysis
- Broad language and framework coverage
- Stable third-party plugin API

These should be designed for, but not implemented in the first MVP.

## 3. Phase 0: Architecture Approval

Duration: 1 week

Deliverables:

- Architecture document approved
- Repository structure approved
- Technical design approved
- MVP roadmap approved
- License selected
- Initial governance rules approved

Exit criteria:

- Maintainers agree on runtime boundaries, MVP scope, persistence baseline, and first supported repository examples.

## 4. Phase 1: Project Foundation

Duration: 2 weeks

Deliverables:

- Python project scaffolding
- CI workflow
- Docker Compose local stack
- FastAPI service skeleton
- CLI skeleton
- Structured logging
- Test framework
- Open-source project files

Exit criteria:

- `docker compose up` starts the API and dependencies.
- `pytest` runs in CI.
- CLI can call a health command.

## 5. Phase 2: Runtime and Tool Framework

Duration: 3 weeks

Deliverables:

- Workflow run model
- Workflow event model
- Artifact model
- Tool contract interface
- Policy and side-effect classification
- Basic artifact store
- Runtime execution loop

Exit criteria:

- A sample workflow can run through multiple steps.
- Events and artifacts are persisted.
- Tool input/output validation is tested.
- External-write tools are blocked without approval.

## 6. Phase 3: RepoAgent MVP

Duration: 3 weeks

Deliverables:

- Repository scanner
- Language and framework detection
- Basic Python FastAPI route detection
- Basic Node.js Express route detection
- Docker and Docker Compose detection
- Repository snapshot persistence
- Repository manifest report

Exit criteria:

- RepoAgent analyzes at least two example repositories.
- Output is stable enough for PerfAgent planning.
- Analyzer tests cover fixture repositories.

## 7. Phase 4: PerfAgent MVP

Duration: 4 weeks

Deliverables:

- Performance target selection
- Test plan generation
- k6 script generation
- k6 validation
- Local k6 execution
- k6 output parsing
- Markdown performance report

Exit criteria:

- PerfAgent runs against an example FastAPI service.
- Generated scripts pass k6 validation.
- A report includes latency, error rate, throughput, threshold status, risks, and next actions.
- Golden-file tests cover report rendering.

## 8. Phase 5: Developer Experience

Duration: 2 weeks

Deliverables:

- `git clone` to first run documentation
- Example repositories
- CLI polish
- Failure diagnostics
- Configuration examples
- Good First Issues

Exit criteria:

- A new contributor can run the first PerfAgent workflow in under 10 minutes on a clean machine with Docker.
- Common failures produce actionable messages.

## 9. Phase 6: GitHub Integration Preview

Duration: 3 weeks

Deliverables:

- GitHub repository metadata reader
- Pull request diff reader
- Dry-run PR comment renderer
- Optional approved PR comment publisher
- GitHub Actions example

Exit criteria:

- PerfAgent can analyze a PR context.
- The system can render the exact PR comment before publishing.
- Publishing requires explicit approval.

## 10. Success Metrics

Developer experience:

- Time to first successful local run: under 10 minutes
- Example workflow success rate: above 90 percent on supported machines
- Clear failure message coverage for known setup issues

Engineering value:

- Detects at least one meaningful performance risk or missing threshold in example repositories
- Generates k6 scripts that run without manual edits for supported examples
- Produces reports that developers can act on without reading raw k6 output

Project health:

- CI is required before merge
- Unit and integration tests are present for core runtime and PerfAgent
- Documentation is sufficient for first-time contributors
- Issues are labeled for newcomers

## 11. Release Plan

### `v0.1.0-alpha`

Focus:

- Local runtime
- RepoAgent MVP
- PerfAgent local report

Audience:

- Early contributors and maintainers

### `v0.2.0-alpha`

Focus:

- GitHub PR context
- Dry-run comments
- Improved examples

Audience:

- Open-source users willing to test early workflows

### `v0.3.0-beta`

Focus:

- Approved PR comments
- Better policy controls
- CI examples

Audience:

- Teams piloting AI performance engineering in non-production workflows

## 12. Approval Checklist

Production code can begin after these are approved:

- Architecture boundaries
- Repository layout
- Runtime and tool contract design
- MVP feature scope
- Security and side-effect policy
- First supported language/framework examples
- License

