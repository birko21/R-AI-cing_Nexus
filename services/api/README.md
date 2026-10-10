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

The application binds to `127.0.0.1` by default. Domain routes currently return bounded synthetic code metadata or empty pages; protected routes fail closed until RIL-010 installs scoped owner authentication. Persistent domain data and fixture ingestion are implemented by later tickets.
