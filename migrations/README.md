# Database migrations

The G1 schema is managed by Alembic and targets local PostgreSQL only. The initial migration is deliberately a forward-compatible relational foundation for synthetic fixtures and future rights-aware providers.

Set `DATABASE_URL` to a loopback disposable database and explicitly confirm
that target before running:

```powershell
$env:DATABASE_URL = 'postgresql+psycopg://user:password@127.0.0.1:5432/racing_intelligence_dev'
$env:RACING_INTELLIGENCE_DB_DISPOSABLE = '1'
pnpm db:upgrade
pnpm db:verify
```

The runner rejects non-PostgreSQL, non-loopback, unconfirmed or ambiguously
named databases before opening a connection. It records a SHA-256 for each
applied migration in `schema_migration_checksums`. Verification fails if a
previously applied migration file changes. The complete disposable smoke is:

```powershell
pnpm db:smoke
```

Do not point these commands at a production or shared database. G0–G3 remains synthetic-only, loopback-only and non-wagering.
