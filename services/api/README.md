# Local API

The API currently exposes the RIL-006 foundation endpoints and the RIL-009 typed route shapes:

- `GET /health/live`
- `GET /v1/system/status`
- `GET /v1/codes`
- `GET /v1/meetings`
- `GET /v1/races/{race_id}`
- `GET /v1/races/{race_id}/entries`
- `GET /v1/races/{race_id}/forecasts`
- `GET|POST /v1/selections`

The application binds to `127.0.0.1` by default. In the default local mode,
domain routes return deterministic `SYNTHETIC_ONLY` meetings, races, entries
and baseline forecasts with point-in-time filtering and signed cursors.
Explicit `NEXUS_API_PERSISTENCE=postgres` selects the PostgreSQL read and
selection repositories and requires a configured database. Protected routes
still fail closed until RIL-010 installs scoped owner authentication.

The offline synthetic ingestion contract is executable through
`services/api/app/ingestion.py`; run
`.\\.venv\\Scripts\\python.exe scripts/run_synthetic_ingestion.py` from the
repository root to process the three-code Betfair-shaped fixture. This uses an
append-only in-memory reference store for local replay and does not activate
external providers. The worker also supports an idempotent canonical projection
hook; the CI backend acceptance run exercises that hook with
`PostgresIngestionStore`, PostgreSQL projections, forecast archives and durable
selection addenda. See `docs/architecture/SYNTHETIC_INGESTION_RUNNER.md` for
the worker boundary and hosted deployment gates.
