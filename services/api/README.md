# Local API

The API currently exposes only the RIL-006 foundation endpoints:

- `GET /health/live`
- `GET /v1/system/status`

The application binds to `127.0.0.1` by default. Domain routes, authentication scopes, migrations and fixture ingestion are implemented by later tickets.
