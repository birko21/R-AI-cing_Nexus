# Remaining epics and execution register

**Plan date:** 2026-10-12  
**Operating boundary:** synthetic-only, read-only, non-wagering, fail-closed

This register is the executable remainder after the completed foundation work.
Tickets marked `COMPLETE` have local implementation and automated evidence.
Tickets marked `BLOCKED_EXTERNAL` or `BLOCKED_HUMAN` are prepared, but cannot
be honestly closed without authority or evidence that is not present in this
repository.

## Epic R1 — Engineering completion and release evidence

| Ticket | Outcome | Status | Evidence |
|---|---|---|---|
| R1.1 | Inventory all remaining engineering, provider and review gates. | COMPLETE | This register and `docs/PROJECT_SPRINT_PLAN.md` |
| R1.2 | Exercise the real worker-to-raw-receipt-to-canonical-projection path. | COMPLETE | `scripts/run_postgres_backend_acceptance.py`, PostgreSQL CI |
| R1.3 | Pressure-test replay, tamper detection, projection replay and retries. | COMPLETE | `scripts/pressure_test_synthetic_pipeline.py` |
| R1.4 | Add one machine-readable safe-completion gate aggregating local evidence and external holds. | COMPLETE | `scripts/validate_safe_completion_gate.py`, `docs/evidence/ril-060/safe-completion-gate.json` |

## Epic R2 — Data-science reproducibility and assurance

| Ticket | Outcome | Status | Evidence |
|---|---|---|---|
| R2.1 | Re-run deterministic RIL-061 benchmark artifacts twice and compare hashes. | COMPLETE | `scripts/pressure_test_data_science.py` |
| R2.2 | Re-run B3 LightGBM/CatBoost synthetic artifacts twice across all three codes. | COMPLETE | `docs/evidence/ril-061/b3-synthetic-evaluation.json` |
| R2.3 | Preserve explicit synthetic-only, non-predictive and no-promotion language. | COMPLETE | B3/RIL-061 evidence and assurance fixtures |
| R2.4 | Obtain independent statistical/model-assurance review and owner decision. | BLOCKED_HUMAN | `docs/models/MODEL_ASSURANCE_WORKFLOW.md` |

## Epic R3 — Hosted operations readiness

| Ticket | Outcome | Status | Evidence |
|---|---|---|---|
| R3.1 | Validate the Render Blueprint, OIDC boundary and provider-disabled defaults. | COMPLETE | `scripts/validate_render_blueprint.py`, Render CI |
| R3.2 | Validate migration, lease, replay, downgrade and re-upgrade behavior against disposable PostgreSQL. | COMPLETE | PostgreSQL CI and `docs/evidence/ril-011/postgres-smoke.md` |
| R3.3 | Prepare hosted database/queue/worker topology, telemetry, retention and cost envelope. | BLOCKED_EXTERNAL | `docs/deployment/RENDER_NEXUS_STAGING.md` |
| R3.4 | Apply or deploy the hosted topology and prove real OIDC access. | BLOCKED_EXTERNAL | Requires owner-controlled Render/Auth0 configuration |

## Epic R4 — Approved provider integrations

| Ticket | Outcome | Status | Evidence |
|---|---|---|---|
| R4.1 | Maintain provider-neutral adapter, capability and entitlement contracts. | COMPLETE | `services/api/app/providers.py`, provider evidence fixtures |
| R4.2 | Prepare source-specific decision packs and reconciliation acceptance criteria. | COMPLETE | `docs/provider/` |
| R4.3 | Activate FormFav, PuntersEdge, Krok or Betfair transports. | BLOCKED_EXTERNAL | Written rights, credentials, retention and model-use approvals absent |
| R4.4 | Validate licensed historical data for walk-forward research. | BLOCKED_EXTERNAL | RIL-077 approval pack |

## Epic R5 — Independent assurance and visual review

| Ticket | Outcome | Status | Evidence |
|---|---|---|---|
| R5.1 | Automated browser, axe, contract, security and no-wagering evidence. | COMPLETE | CI matrix and S4 packet |
| R5.2 | Independent accessibility, racing-domain, model-assurance and security-owner decisions. | BLOCKED_HUMAN | S4 review gates |
| R5.3 | Visual-owner comparison of the approved V7 reference set. | BLOCKED_HUMAN / LAST | Deliberately held until executable paths are accepted |

## Epic R6 — Controlled pilot handover

| Ticket | Outcome | Status | Evidence |
|---|---|---|---|
| R6.1 | Produce an immutable release manifest and no-regression checklist. | READY | Existing S4/release-gate artifacts are prepared |
| R6.2 | Record owner-approved restricted pilot scope and go/no-go decision. | BLOCKED_HUMAN | `docs/evidence/ril-060/release-gate-checklist.md` |
| R6.3 | Deploy a public or live-provider pilot. | BLOCKED_EXTERNAL | Explicitly out of scope until R3/R4/R5 gates pass |

## Completion rule

R1–R3 local tickets and R4.1–R4.2/R5.1 are complete in this branch. The
remaining tickets are not safe to simulate: they require provider contracts,
credentials, hosted resources, independent reviewers or owner approval. No
ticket in this register grants activation, wagering, promotion or deployment
authority.
