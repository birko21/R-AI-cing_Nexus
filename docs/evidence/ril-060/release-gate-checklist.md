# RIL-060 release gate checklist

Status: `LOCAL_EVIDENCE_COMPLETE_OWNER_APPROVAL_PENDING`

Observed evidence:

- Responsive UX and keyboard/screen-reader journey: `pnpm exec playwright test` — exit code 0; 5 passed. Existing screenshots include `docs/evidence/ril-017/`, `ril-018/`, `ril-019/`, `ril-020/`, `ril-040/` and `ril-049/`.
- Web static checks: `pnpm --filter @racing-intelligence/web typecheck` — exit code 0; `pnpm --filter @racing-intelligence/web build` — exit code 0.
- API and degraded-source checks: `.venv\\Scripts\\python.exe -m pytest services/api/tests -q` — exit code 0; 212 passed, one existing Starlette/AnyIO deprecation warning.
- Synthetic fixture and repository checks: `scripts/seed_fixture.ps1` — exit code 0; `scripts/validate_repository.ps1` — exit code 0; G0 / BLOCKED, 258 required files.
- Security: `scripts/security_audit.py --write-report` — PASS; 0 secret findings and 0 frontend-secret references. SBOM is `docs/evidence/ril-057/sbom.json`.
- Restore/provenance: `docs/evidence/ril-059/backup-restore-transcript.json`, synthetic provenance fixtures and hash checks are present.
- Safety: no-wagering tests, responsible-use controls, egress controls and explicit `NOT_AVAILABLE` degraded states are present and covered by the API/UI suites.

Restricted pilot scope: local synthetic-only demonstration; no production bind, approved OIDC, live provider, licensed feed, external LLM, bookmaker credential or wagering action.

Unresolved risks:

1. RIL-056 / issue #69: owner-approved OIDC issuer, signing/JWKS, audience and scope mapping are not supplied; production/public auth remains fail-closed.
2. RIL-034 / issue #47: written real-source rights, retention, model-use, display and reconciliation evidence remain missing.
3. Owner approval for the restricted pilot scope has not been recorded.

Owner decision: `PENDING_OWNER_APPROVAL`.
