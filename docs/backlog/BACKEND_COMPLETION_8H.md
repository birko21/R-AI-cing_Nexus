# Backend completion sprint — eight-hour execution register

**Scope:** backend, data plane, provider safety, contracts, testing and
deployment only. Visual-owner review remains last and is intentionally excluded.

**Operating boundary:** synthetic by default; real-provider work is read-only,
bounded and fail-closed. No wagering, trading, staking, order placement,
automatic actions or model promotion are included.

## Sprint exit definition

The backend is considered engineering-complete when the local and staging
paths have reproducible evidence for API contracts, authentication, provider
gating, ingestion, provenance, replay, PostgreSQL persistence, model
reproducibility, security and deployment health. A provider-backed result is
not claimed until an owner-configured approval record and real response sample
exist.

## Tickets completed in this sprint

| Ticket | Outcome | Evidence |
|---|---|---|
| BE-011 | Expose non-secret runtime readiness for all four provider credentials, flags, diagnostics and approval state. | `/v1/system/status`; commit `09c8e33` |
| BE-012 | Add a dedicated `providers:read` authorization scope. | `services/api/app/auth.py`; contract and auth tests |
| BE-013 | Add a PuntersEdge aggregate-only probe endpoint with a two-request ceiling: account metadata first, then one bounded read. | `/v1/provider-probes/punters-edge`; commit `f20f877` |
| BE-014 | Guarantee probe responses never retain or return raw provider payloads. | `ProviderDiagnosticCheck`; negative tests |
| BE-015 | Normalize provider HTTP failures, transport failures and malformed JSON into safe activation errors. | `test_external_provider_integrations.py` |
| BE-016 | Deploy the backend-only staging branch without active visual source changes. | Render deployment `dep-db7n2qm7bikc73bfbk4g`; health `ok`; no error logs |
| BE-017 | Re-run full backend, contract, repository and lint validation after the changes. | 325 API tests passed; Ruff, contract, security, repository and synthetic pressure checks passed. |

## Remaining execution tickets

| Ticket | Acceptance | Status |
|---|---|---|
| BE-018 | Configure one provider's explicit enable flag, diagnostics flag, two non-secret diagnostic approval records and `providers:read` owner permission. | Owner/Render configuration required; no secret values in source or chat. | BLOCKED_EXTERNAL |
| BE-019 | Execute the first bounded PuntersEdge diagnostic and retain only aggregate evidence. | Requires BE-018 and an owner-authorized token. | BLOCKED_EXTERNAL |
| BE-020 | Execute one approved live capture, validate schema/identity/timestamps and persist only where retention rights and PostgreSQL are approved. | Requires real provider response, rights record and database target. | BLOCKED_EXTERNAL |
| BE-021 | Reconcile live provider rows into canonical meetings, races and entries with quarantine for identity/timestamp/rights failures. | Requires BE-020 sample and provider-specific parser acceptance. | BLOCKED_EXTERNAL |
| BE-022 | Run chronological walk-forward evaluation on approved historical data and compare B0–B4 baselines. | Requires approved retention/model-use rights and sufficient labelled history. | BLOCKED_EXTERNAL |
| BE-023 | Provision hosted PostgreSQL plus worker/queue topology and run migration, backup, restore and soak evidence. | Render currently has no database/queue and the service is on the Free plan. | BLOCKED_EXTERNAL |
| BE-024 | Produce the final non-visual release gate and handover. | Requires BE-019–023 plus independent security/model/domain decisions. | READY_AFTER_EXTERNAL_GATES |

## Future epics required after this sprint

### F1 — Provider activation and canonical live data

BE-018 through BE-021. This epic cannot be honestly completed from credentials
alone; it requires provider-specific rights, bounded responses, identity
reconciliation and retention evidence.

### F2 — Real-data model assurance

BE-022 plus independent statistical/model review. Synthetic benchmark results
remain illustrative and cannot be relabelled as validation.

### F3 — Hosted operations

BE-023: managed PostgreSQL, durable worker execution, queue/lease recovery,
telemetry, backups, restore, quotas and cost controls.

### F4 — Restricted pilot release

BE-024 plus owner, accessibility, racing-domain, security and visual-owner
decisions. This is deliberately last for visual work.

## Current measured state

The staging service reports all four credential sets configured, all provider
enable flags false, diagnostics false and approval records absent. This is the
correct safe state. The live probe route therefore rejects activation until the
external gate is satisfied; no live recommendation claim is made.

## Final verification record

This section is append-only evidence for the current sprint. Commands and
results are recorded only after execution; a failed or blocked check is not
described as passing.

- `python -m pytest -q services/api/tests` — `325 passed in 22.96s`
- `python -m ruff check services/api/app services/api/tests scripts` — `All checks passed`
- `python scripts/validate_contracts.py` — `CONTRACT VALID: openapi_paths=10 schemas=24`
- `python scripts/security_audit.py` — `SECURITY AUDIT PASS: files=396 secret_findings=0 frontend_secret_refs=0`
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate_repository.ps1` — `VALID CHECKPOINT: G0 / BLOCKED`; `REPOSITORY BASELINE VALID: 375 required files present`
- `python scripts/pressure_test_synthetic_pipeline.py` — `PASS`, 25 cycles, deterministic replay, 25 tamper cases
- `python scripts/pressure_test_data_science.py` — synthetic evidence valid for six model/code combinations; no real-data validation claim
- `python scripts/prove_synthetic_vertical.py` — `PASS`; ingestion replay idempotent, forecast archive replay matched, release gate `LOCAL_SYNTHETIC_ONLY_HOLD`
- Staging black-box check against `https://nexus-staging-api-feap.onrender.com` — health `ok`; `data_mode=SYNTHETIC_ONLY`; `external_connectivity=false`; all four provider flags/diagnostics disabled; `providers:read` probe without a token returned `401`; OpenAPI exposed the probe route.
- Render error-log query for `nexus-staging-api` — zero error logs returned.

The local PostgreSQL acceptance script remains environment-blocked because this
machine has no disposable database credentials available to the repository
test harness. The existing database acceptance evidence is retained, and the
hosted database/backup/restore ticket remains external rather than being
marked complete without a real target.
