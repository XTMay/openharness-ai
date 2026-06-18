# RepoAgent Configuration

RepoAgent works without configuration, but real repositories often need local context.

Add `openharness.yaml` at the repository root to customize analysis.

## Example

```yaml
ignore:
  - "generated/**"
  - "migrations/**"

service_roots:
  - "app"
  - "services/api"

production_paths:
  - "app"
  - "src"

performance:
  business_critical_keywords:
    - "checkout"
    - "order"
    - "payment"
    - "search"
```

## Fields

### `ignore`

Glob patterns excluded from scanning.

Use this for generated code, migrations, fixtures, snapshots, or large local artifacts.

```yaml
ignore:
  - "generated/**"
  - "migrations/**"
  - "fixtures/large/**"
```

### `service_roots`

Directories that contain service code.

When set, RepoAgent only extracts frameworks, API routes, and service entrypoints from these paths. Language and package-manager detection still scans the repository, after ignore rules.

```yaml
service_roots:
  - "backend"
  - "services/api"
```

### `production_paths`

Directories that contain production source code.

This is useful for repositories that include tools, examples, experiments, or generated clients next to production services.

```yaml
production_paths:
  - "src"
  - "app"
```

### `performance.business_critical_keywords`

Keywords used to rank performance target candidates.

Routes containing these keywords are ranked as high-priority candidates.

```yaml
performance:
  business_critical_keywords:
    - "checkout"
    - "payment"
    - "order"
```

## Backward Compatibility

If no config file exists, RepoAgent uses built-in defaults.

Supported filenames:

- `openharness.yaml`
- `openharness.yml`

The configuration summary is included in every JSON and Markdown manifest so downstream agents can see which rules were applied.

