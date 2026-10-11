# RIL-011 / T-A PostgreSQL smoke evidence

The repository now executes the durable synthetic ingestion database path in
the `postgres-smoke` GitHub Actions job. The job provisions an isolated
PostgreSQL 16 service and sets:

```text
DATABASE_URL=postgresql+psycopg://nexus:nexus@127.0.0.1:5432/racing_intelligence_dev
RACING_INTELLIGENCE_DB_DISPOSABLE=1
```

The job verifies, in order:

1. The database target is loopback-only, PostgreSQL, explicitly disposable,
   and named as a development database.
2. Alembic upgrade, migration checksum recording, checksum verification, and
   the `ingestion_jobs` schema.
3. A repeated synthetic PostgreSQL ingestion run with the same replay
   identifier, followed by a separate replay identifier, exercising durable
   enqueue/claim/persist completion and idempotent replay behavior.
4. Alembic downgrade to base, clean upgrade to head, and final checksum/schema
   verification.

The local `pnpm db:smoke` command remains fail-closed unless the operator
supplies an explicitly disposable loopback `DATABASE_URL`. This evidence is
synthetic-only and grants no provider activation, production deployment, or
model-promotion authority.
