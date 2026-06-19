# FastAPI Example Service

This is a small example repository used to verify RepoAgent behavior.

Run RepoAgent against it:

```bash
openharness analyze --repo examples/fastapi-service --format text
openharness analyze --repo examples/fastapi-service --format markdown
openharness perf plan --repo examples/fastapi-service --format markdown
openharness perf generate --repo examples/fastapi-service --output .openharness/k6 --format text
openharness perf validate --artifacts .openharness/k6
```

The service intentionally includes health, catalog, order, and checkout routes so RepoAgent can detect API routes and performance target candidates.

This example also includes `openharness.yaml` to demonstrate:

- ignoring generated and migration paths
- limiting service analysis to `app`
- ranking `checkout`, `order`, and `products` routes as business-critical performance targets
