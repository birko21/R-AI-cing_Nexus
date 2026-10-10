# Racing Intelligence Lab — Product + Technical Master Specification v1.1
**Effective 10 October 2026** · Source of truth for the initial Codex handover.

## Objective
Deliver a genuine offline, responsive Australian thoroughbred/harness/greyhound research application that can demonstrate three-code field browsing, as-of historical integrity, explicit analyst selections/PASS and a deterministic race-normalised model baseline. The offline MVP must be **operational**, **synthetic-only**, **non-wagering** and **non-validated**; it makes no claim of real-world accuracy or profitability.

## Documents that together constitute the master specification
1. `docs/OFFLINE_MVP_SCOPE.md` — functional scope, gates G0–G3 and completion proofs.
2. `docs/STATISTICAL_CONTRACT.md` — formal targets and evidence semantics; precise edge cases.
3. `migrations/001_offline_mvp.sql` — initial relational schema and DB integrity constraints.
4. `contracts/openapi_mvp.yaml` — API paths, inputs/outputs, auth scopes, errors and paging.
5. `docs/STATUS_AND_GATES.md` — single source of truth for status terms.
6. `docs/DECISION_REGISTER.md` — approvals, explicit unknowns and default no-spend/no-egress.
7. `CODEX_EXECUTION_PROMPT_V1_1.md` — delivery execution and evidence contract.
8. `DATA_PROVIDER_DUE_DILIGENCE.md` — questionnaire for later licensed feeds.
9. `MASTER_SPEC_V1_0_REFERENCE.md` — comprehensive subsequent product vision only.

The supplied fixture set has a fixed **fictional demo date**; Codex must support a labelled demo-date selector or deterministic time-shifted seeding for a current-date UI, without representing the generated fixture as real racing data.

All of these constitute one *versioned* specification. Codex must not silently replace contractual requirements with future-vision suggestions. Architecture changes require ADRs and coherent changes to code/tests/contracts.

## V1.0-to-v1.1 conflict resolution
| Old requirement / interpretation | Binding v1.1 interpretation |
|---|---|
| Implement full original G0–G11 | G0–G3 only as the bounded active MVP. Original stage numbers superseded. |
| G0–G3 stop at a UI-only demo | G3 now includes baseline probability engine + evaluation + temporal replay |
| Three-code advanced predictive models essential immediately | Simple explicitly unvalidated B0/B1 per-code demonstration initially; advanced modelling deferred |
| Live data integration needed to show complete product | All three codes demo offline, no market prices and **no external connectivity** |
| `PUBLICLY_VERIFIED` provider route | Interpret solely as `PUBLIC_CLAIM_PENDING_REVERIFICATION`; **never evidence of entitlement** |
| Status variants inconsistent between documents | `docs/STATUS_AND_GATES.md` controls release, model and gate statuses |
| Generic API schemas, no formal authorisation | OpenAPI 3.1 routes, bearer scopes and response schemas control; scopes enforced server-side |
| Logical ERD only | Executable draft local Postgres migration + migration acceptance smoke in G1 |
| Dead-heats/coupled entries unspecified | G3 excludes ties from primary scoring and abstains on coupled groups |
| Vague confidence and model promotion | Synthetic-only no confidence tier; prospective G7 criteria and human approval |
| Unknown timestamp treated as likely present | No verifiable publication/receipt proof = exclude from point-in-time input/evaluation |

## Architecture (initial, modular monolith)
`React/Vite browser (localhost)` ↔ `FastAPI (loopback, scopes)` ↔ `PostgreSQL (local)`; one library for synthetic receipt ingestion + as-of features + deterministic B0/B1 calculation; no background queues required in G0–G3. The private owner journal is stored server-side. Deployment resources, OIDC provider, licensed data feeds, market-data source, object storage, cloud backups and third-party LLM provider are **not approved**.

### Authentication boundary
`/v1/system/status` can be accessed anonymously and must reveal **only configuration status**, no private data, credentials or operational secrets. Every other API operation requires bearer authentication and server-authorised scopes from the OpenAPI contract. G0–G3 local signing keys/tokens must come from env and never be checked into Git. Dev mode is permitted **only on loopback** when `APP_ENV=development` and `ALLOW_LOCAL_AUTH=true`; application startup rejects any external bind/public deployment without configured owner-approved production OIDC. Later OIDC issuer/audience/key validation is an explicit separate gate, not assumed completed.

### Pagination and time
List endpoints return a bounded maximum 100 elements; default limit=25; stable keyset sorting; non-forgeable cursor containing the effective `as_of` and filters; mismatched/modified cursors yield `400 BAD_REQUEST`, not alternative results. Detail/list snapshots are based on actual durable first-observation proof. The frontend displays Australia/Sydney local times; persisted times retain UTC instants.

### Provenance
Every fixture and eventual licensed row needs an immutable source receipt with checksum, first observation, publication (nullable) and rights state. Synthetic fixtures declare simulated times and cannot be compared as a real event dataset. Corrected results/fields append new revisions. Archived forecasts and selections never update in place. Current field validity can change as a derived status.

### Model and science
B0 equal probabilities and code-aware B1 illustrative probabilities are the only G3 model requirements. Every forecast records the specific field revision, cutoff, model version and manifest checksum. Unsupported coupled entry, incomplete field, nonfinite probability or insufficient timing proof fails closed. Only officially resolved `SINGLE_WINNER` races receive primary log-loss/Brier calculations; exclusions are surfaced. The term `MODEL_VALIDATED` cannot be used for any G3 model, regardless of observed synthetic performance.

### Functional acceptance
See `docs/OFFLINE_MVP_SCOPE.md` for exact gates and stories MVP-01–10. The master is considered **implemented** only when Codex records passing test outputs, local database migration evidence, browser screenshots, model manifest replay and audit of security/rights rules. This document/package itself is a specification, not the implementation.

## Deferred comprehensive ambition
Retain the following for later after permissions and test evidence: historical sectional analysis, code-specialist models, walk-forward calibration and uncertainty, proper win/place/exotic settling probabilities, market intelligence, a model championship, race-shape simulations, AI research agents, notifications and real deployment. Their full background detail remains in `MASTER_SPEC_V1_0_REFERENCE.md`, but none is implied by `OFFLINE_MVP_READY`.
