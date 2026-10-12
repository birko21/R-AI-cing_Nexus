# Backend acceptance and pressure evidence

The backend completion increment closes the placeholder read path for the
synthetic mode and adds an explicit PostgreSQL composition:

- `app.catalog_repository` serves meetings, races, entries and forecasts with
  point-in-time filtering and signed cursor pagination;
- `app.synthetic_projection` projects validated synthetic envelopes into the
  canonical PostgreSQL identity tables and forecast archive;
- `PostgresSelectionJournal` persists append-only selections and addenda;
- `scripts/run_postgres_backend_acceptance.py` verifies three-code PostgreSQL
  projections, forecast reads and durable selection persistence; and
- `scripts/pressure_test_synthetic_pipeline.py` repeats replay processing for
  25 cycles, regenerates the replay manifest 25 times and exercises 25 tamper
  cases.

The default API mode remains deterministic `SYNTHETIC_ONLY`. PostgreSQL mode
requires explicit `NEXUS_API_PERSISTENCE=postgres`, a configured database and
the full migration set. No provider credential or external transport is
enabled by this work.

The acceptance boundary is intentionally narrow: it proves persistence,
identity, temporal filtering, replay and fail-closed behaviour. It does not
claim licensed provider access, real-world model accuracy or production
approval.
