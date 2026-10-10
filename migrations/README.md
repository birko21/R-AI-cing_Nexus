# Database migrations

The G1 schema is managed by Alembic and targets local PostgreSQL only. The initial migration is deliberately a forward-compatible relational foundation for synthetic fixtures and future rights-aware providers.

Set `DATABASE_URL` to a disposable local database before running:

```powershell
$env:DATABASE_URL = 'postgresql+psycopg://user:password@127.0.0.1:5432/racing_intelligence_dev'
pnpm db:upgrade
pnpm db:verify
```

The runner records a SHA-256 for each applied migration in `schema_migration_checksums`. Verification fails if a previously applied migration file changes. The disposable rollback/forward smoke is:

```powershell
pnpm db:downgrade
pnpm db:upgrade
pnpm db:verify
```

Do not point these commands at a production or shared database. G0–G3 remains synthetic-only, loopback-only and non-wagering.
