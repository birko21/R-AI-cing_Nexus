# Local development

RIL-006 provides a reproducible Windows-first local bootstrap for the offline MVP foundation. The application is intentionally loopback-only and synthetic-only at this stage.

## Prerequisites

- Windows PowerShell 5.1 or PowerShell 7.
- Node.js 22.x or later and pnpm 11.19.0. The root `package.json` pins the package manager version.
- Python 3.11–3.13. The API package rejects unsupported Python versions.
- PostgreSQL 18 running locally and accepting TCP connections on `127.0.0.1:5432`. The bootstrap checks the standard Windows installation path for `pg_isready.exe`.
- Playwright 1.64.0 or later for browser tests. Install the browser binary when browser tests are introduced:

  ```powershell
  npx --yes playwright install chromium
  ```

Docker is not required for the current Windows bootstrap. Cloud services, licensed racing feeds, external LLMs, OIDC and public scraping remain outside the active G0–G3 MVP.

## Bootstrap

From the repository root:

```powershell
pnpm bootstrap
```

The command checks Node, Python, pnpm and PostgreSQL, creates `.venv`, installs the pinned API development dependencies, and installs the locked web dependencies. It fails on dependency installation errors.

## Run and validate

```powershell
pnpm seed:fixture
pnpm dev
```

The API is available at `http://127.0.0.1:8000` and the Vite web shell at `http://127.0.0.1:5173`. The current API checks are:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health/live
Invoke-RestMethod http://127.0.0.1:8000/v1/system/status
```

Frontend checks and the repository baseline check are:

```powershell
pnpm web:check
pnpm web:build
pnpm api:test
pnpm validate
```

The API contract is in `contracts/openapi_mvp.yaml`; its hand-checked TypeScript types are in `contracts/types.ts`. The fixture command only verifies the bootstrap manifest. Full three-code synthetic records are delivered by RIL-016.

## Database migration foundation

Set `DATABASE_URL` to a disposable local PostgreSQL database using the `postgresql+psycopg://` scheme, then run `pnpm db:upgrade`. The migration runner records and verifies SHA-256 checksums. Use `pnpm db:downgrade` followed by `pnpm db:upgrade` for the forward/rollback smoke; never point this smoke at a shared or production database.
