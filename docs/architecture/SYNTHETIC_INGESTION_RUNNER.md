# Synthetic ingestion runner

## Purpose

The active MVP remains local and synthetic-only. This runner makes the data
processing contract executable without activating a real provider or requiring
a broker, cloud worker, or external network connection.

Implementation: `services/api/app/ingestion.py`.

Run it locally with:

```powershell
.\.venv\Scripts\python.exe scripts/run_synthetic_ingestion.py
```

The command processes all three synthetic racing codes and prints a JSON run
summary. Use `--code THOROUGHBRED --page-size 1` to exercise a bounded single
code run, or repeat `--code` for a selected set.

After migrations have been applied to an explicitly disposable loopback
database, the same worker can run through the durable PostgreSQL repository:

```powershell
$env:DATABASE_URL = 'postgresql+psycopg://user:password@127.0.0.1:5432/racing_intelligence_dev'
$env:RACING_INTELLIGENCE_DB_DISPOSABLE = '1'
.\.venv\Scripts\python.exe scripts/run_postgres_synthetic_ingestion.py --replay-id local-run
```

The command validates the target before opening a connection and uses no real
provider, credentials or external network. `pnpm db:smoke` runs this durable
worker path as part of the disposable upgrade/checksum/schema/
downgrade/re-upgrade sequence.

The worker consumes a `ContractedProviderAdapter`, one bounded page at a time,
and performs the following sequence:

```text
enqueue → claim → bounded adapter fetch → envelope validation
        → append-only persistence or quarantine → pagination continuation
        → terminal job state
```

## Guarantees

- Only adapters declaring `SYNTHETIC_ONLY` data and `SYNTHETIC` rights are
  accepted by this local worker.
- Every page is bounded by the adapter contract and has a serializable job
  identity.
- The idempotency key is provider, operation, code, replay ID and cursor. A
  duplicate enqueue returns the original job rather than creating work twice.
- Raw envelopes are append-only. Replaying the same envelope is a skip; the
  same envelope ID with a different checksum is quarantined as an unresolved
  identity conflict.
- Adapter failures retry up to the configured attempt limit and then become a
  terminal `FAILED` job.
- A returned cursor creates a deterministic continuation job; the worker does
  not fetch an unbounded result set in one run.
- No login, credential resolution, outbound transport, order, staking,
  wagering, or live-provider activation is available through this module.

## Deliberate scope boundary

`InMemoryIngestionStore` is an offline reference implementation for the worker
contract and tests. `PostgresIngestionStore` maps the same operations to the
existing append-only PostgreSQL tables:

- `raw_envelopes` and `quarantine_records` from migration 005;
- `source_capability_controls` from migration 006;
- bitemporal revisions from migration 004;
- source health events from migration 009.

Migration `019_ingestion_jobs` defines the durable queue state and lease
columns. A separate external scheduler or broker remains a later increment;
the v1.1 active MVP explicitly does not require one in G0–G3.

The lease protocol is bounded and restart-safe: a worker claims one eligible
job with `FOR UPDATE SKIP LOCKED`, sets a lease owner and expiry, and a later
worker may reclaim an expired lease. The caller must commit the transaction;
the repository does not hide transaction boundaries.

## Evidence

`services/api/tests/test_ingestion.py` covers three-code ingestion, replay
idempotency, pagination, retry exhaustion, synthetic-only enforcement, and
checksum-conflict quarantine.
