# FastAPI Example Service

This is a small example repository used to verify RepoAgent behavior.

Run RepoAgent against it:

```bash
openharness analyze --repo examples/fastapi-service --format text
openharness analyze --repo examples/fastapi-service --format markdown
```

The service intentionally includes health, catalog, order, and checkout routes so RepoAgent can detect API routes and performance target candidates.
