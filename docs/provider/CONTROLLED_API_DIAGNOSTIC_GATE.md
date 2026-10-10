# Controlled API diagnostic gate

Status: **PREPARED, DISABLED**  
Scope: existing FormFav, PuntersEdge, Krok Odds and Betfair accounts only  
PR governance: PR #75 remains unchanged at `8dce999194eb4e17a1404dba54d03fa18f749e6d`; this gate is developed on a separate local branch while independent review is pending.

## Decision

Account access does not grant model-use rights. Nexus therefore separates
provider approval into three non-transitive tiers:

1. `ACCOUNT_METADATA_READ` — account plan, entitlement and quota metadata only;
2. `EPHEMERAL_READ_ONLY_DIAGNOSTIC` — bounded response-shape and data-quality
   inspection, aggregate output only and no raw retention;
3. `HISTORICAL_RETENTION_AND_MODEL_TRAINING` — the only tier that can create
   licensed model-ingest envelopes, and only after written retention, training,
   calibration, evaluation and derived-display evidence.

An approval at tier 1 or 2 cannot be used to train a model, retain historical
payloads, calibrate forecasts or display derived predictions.

## Evidence and current entitlement decision

| Provider | Exact evidence available | Permitted now in Nexus | Explicitly blocked |
|---|---|---|---|
| PuntersEdge | Sibling sanitized account metadata recorded `plan=free`, key creation `2026-09-24`; a bounded Randwick 2026-09-19 result sample returned 10 final AU thoroughbred races, 9 complete, fixed Win/Place fields and 2,990 credits remaining. | No live operation yet. Candidate for separately approved metadata and ephemeral diagnostic tiers. | Historical retention, ML training, calibration, evaluation, derived display and automatic promotion. |
| FormFav | Sibling server-only key pattern and AU gallops card adapter; owner confirms existing account/API access. | No live operation yet. Technical card-read shape only. | Historical storage, model use, derived display and unsupported racing codes. |
| Krok Odds | Sibling authenticated read-only probes returned HTTP 200 at `api` tier; finishing rows were available, but complete tote/BSP settlement evidence was absent. | No live operation yet. Technical enrichment/results shape only. | Historical storage, model use, derived display without a Nexus-specific rights record. |
| Betfair Exchange | Sibling read-only catalogue/book authentication and AU horse event type 7 response shapes. | No market connectivity. Synthetic fixture only. | All live market catalogue/book access, historical prices/liquidity retention, training, calibration and derived display. |

These are sanitized repository/documentation facts, not a fresh account login.
No secret, production environment or raw response was read. The Long Straight
was not modified.

## PuntersEdge approval and diagnostic record

| Decision field | Recorded value |
|---|---|
| Provider | PuntersEdge |
| Racing code | `THOROUGHBRED` only |
| Known sample | `2026-09-19`, `Randwick`, Australian horse results |
| Exact diagnostic operations | `GET /v1/keys/info`; `GET /v1/racing/results` for the known sample; one owner-approved earlier/boundary date; up to three `GET /v1/racing/horses/form` requests for runners returned by the known sample |
| Maximum HTTP requests | 6 total: 1 metadata + 2 results + 3 form |
| Pagination | Prohibited |
| Retries | Prohibited; a failed request consumes its ordinal and the session ends |
| Current quota check | Must be request 1 and must expose plan/credits/quota fields; absence fails closed |
| Credit ceiling | No open-ended credit use. The sanitized historical observation was 2,990 remaining; the current value is not assumed and must be read at request 1. The six-request ceiling is an additional hard limit. |
| Credential custodian | **Pending named owner record**; only a server-side resolver may supply credentials |
| Kill switch | `DiagnosticPolicy(enabled=False)` plus the default registry having no transport or credential resolver |
| Raw retention | Prohibited by diagnostic policy; only aggregate metadata may be retained |
| Training/calibration/display | Prohibited until tier 3 approval |

The known sample is a diagnostic target, not permission to execute. The owner
must supply distinct records for `ACCOUNT_METADATA_READ` and
`EPHEMERAL_READ_ONLY_DIAGNOSTIC`, each naming the provider, operation, code,
credential custodian, quota ceiling and kill-switch reference.

## Sanitized diagnostic output contract

`SanitizedDiagnostic` may contain only:

- provider ID, operation, racing code and request ordinal;
- HTTP status class, aggregate row count and bounded field-presence names;
- whether quota metadata was observed;
- `raw_payload_retained=false` and the approval reference.

It must not contain API keys, authorization headers, raw URLs with secrets,
runner names, runner IDs, raw timestamps, raw prices, raw provider errors or
raw payloads. A diagnostic response cannot be passed to the historical feature
pipeline.

## Implementation controls

- `SourceApprovalRecord` now carries an explicit approval tier and named
  operation/code scope.
- `evaluate_tiered_source_approval` checks tier-specific evidence.
- `GatedReadOnlyProviderAdapter.fetch` requires
  `HISTORICAL_RETENTION_AND_MODEL_TRAINING` and remains unreachable from the
  default disabled registry.
- `BoundedDiagnosticSession` requires separate metadata and ephemeral approval
  records, enforces the six-request ceiling, requires metadata first, rejects
  pagination and exposes no retry path.
- `DiagnosticPolicy` cannot enable raw persistence or model training.
- Betfair remains disconnected; no live market transport is constructed.

## Blocked operations

Until tier 3 approval is recorded, Nexus must reject:

- persistence of historical provider payloads or feature snapshots;
- form, market or combined model training;
- calibration and out-of-sample evaluation using provider data;
- derived forecast display or export;
- Betfair catalogue/book/price/liquidity connectivity;
- credentials in frontend code, logs or source control;
- wagering, staking, trading or automated model promotion.

The implementation and tests use only fake transport data. No live request was
executed for this gate.
