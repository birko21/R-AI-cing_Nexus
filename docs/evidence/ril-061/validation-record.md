# RIL-061 continuation validation record

## Local evidence

| Command | Exit code | Result |
|---|---:|---|
| `.venv\Scripts\python.exe -m pytest services/api/tests -q` | 0 | 235 backend tests passed; one existing Starlette/AnyIO deprecation warning |
| `.venv\Scripts\python.exe -m ruff check services/api/app services/api/tests scripts` | 0 | Ruff passed |
| `.venv\Scripts\python.exe scripts/validate_contracts.py` | 0 | 9 OpenAPI paths and 20 schemas validated |
| `.venv\Scripts\python.exe scripts/security_audit.py` | 0 | No secret findings or frontend secret references |
| `.venv\Scripts\python.exe scripts/generate_ril061_evidence.py` | 0 | Synthetic RIL-061 evidence regenerated |
| `.venv\Scripts\python.exe scripts/generate_b3_synthetic_evidence.py` | 0 | Six B3 synthetic backend/code evaluations regenerated |
| `.venv\Scripts\python.exe -m pip install lightgbm==4.7.0 catboost==1.2.10` | 0 | Local development-only ML dependencies installed; lock file records transitive pins |
| `pnpm run web:check` | 0 | Frontend typecheck passed |
| `pnpm run web:build` | 0 | Production frontend build passed |
| `pnpm run web:e2e` | 0 | Six browser/accessibility smoke tests passed; workbench screenshot generated |
| `pnpm run validate` | 0 | Repository baseline validation passed after final staging |

## Safety boundary

The branch contains no provider credentials, no live network adapter activation, no production deployment, no wagering/staking/trading execution and no automatic model promotion. Synthetic B3 results remain `ILLUSTRATIVE_SYNTHETIC_ONLY`.

## Remote evidence status

The CI workflow is committed on the feature branch and is intended to run on push and pull request. A remote CI run and pull request URL are recorded only after GitHub accepts the branch publication; no branch protection is bypassed and no merge is automated.
