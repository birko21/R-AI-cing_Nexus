# Existing API activation readiness

Status: **READY FOR CONTROLLED APPROVAL, EXTERNAL CONNECTIVITY DISABLED**

This report is an implementation-readiness audit of the four provider assets
already present in `KirkMathie/The-long-straight`. It is not a procurement
proposal. The read-only audit snapshot was commit
`3ce0da06605e01d93d48398dc8ed471aa5c294f3`, inspected on 10 October 2026.
The sibling checkout remained unchanged. No credentials or production
responses were copied into Racing Intelligence Lab.

## Executive decision

All four providers have a usable technical adapter shape for an Australian
thoroughbred pilot, but none is activated in Nexus. Account access is not the
same as permission to retain, train, calibrate, evaluate or display derived
forecasts in this application. Nexus now has provider-specific endpoint
contracts, bounded probe plans, common envelopes and a fail-closed activation
gate. The default registry contains no transport and loads no credentials.

The quickest evidence-backed first experiment is a two-request PuntersEdge
thoroughbred probe: one date/venue results request and one horse-form request.
The sibling contains sanitized real-response evidence for that shape and a
personal free-plan observation. Before persistence or modelling, the owner
must record Nexus-specific rights and the named operation/code approval. This
probe must not be run from the application until that record exists.

## Provider readiness matrix

| Provider | Technical assets evidenced | Historical/feature reality | Account and cost evidence | Rights state for Nexus | Minimal activation scope |
|---|---|---|---|---|---|
| FormFav | `GET /v1/form/meetings`, `GET /v1/form`; AU gallops/thoroughbred cards | Meetings, distance, class, start time, runner, barrier, jockey, trainer, weight, form and scratch flag. No result, sectional, speed or market adapter. No earliest historical date evidenced. | Owner confirms account/API access. Plan, quota and price were not recorded in sibling evidence. | **TECHNICALLY_AVAILABLE_RIGHTS_PENDING**. Sibling private-use terms do not transfer. | `LIST_MEETINGS` and `GET_RACES`, one date/venue, no persistence until rights record. |
| PuntersEdge | `/v1/racing/results`, `/v1/racing/horses/form`; account-info probe existed in sibling | Results/form, start/result timestamps, runner identity, position, dead-heat flag and fixed Win/Place prices. No sectionals or exchange liquidity evidenced. Sanitized probe: 10 final races, 9 complete. Earliest durable export date unknown; 2026-09-19 is only an observed sample. | Personal free-plan observation with 2,990 credits remaining after the bounded probe; current quota/cost must be confirmed from the account evidence used for Nexus. | **TECHNICALLY_AVAILABLE_RIGHTS_PENDING**. Personal-use authorization is not Nexus model/retention/display authorization. | `GET_RESULTS` and `GET_ENTRIES`, one date/venue plus one form sample. |
| Krok Odds | Meetings, `odds-feed/racing`, runner-form, date-scoped results and tote-pool validation targets | Runner/form and market enrichment, distance, barrier, jockey, trainer, recent finishes and sectionals where returned. Sibling recheck did not establish complete numeric tote/BSP values or durable history. Earliest date unknown. | Sibling documentation reports free A$0, 50 credits/month and 5 requests/minute; observed credential was `api`, not proven free. Current quota/overage must be verified from the owner account. | **TECHNICALLY_AVAILABLE_RIGHTS_PENDING**. Key and intended-use review are not Nexus training rights. | Meetings, runner-form, odds and results as separate bounded operations after rights approval. |
| Betfair Exchange | Login plus read-only `listMarketCatalogue` and `listMarketBook`; AU horse event type 7 | Catalogue identity, runner IDs, market start time, read-only price/available/matched-volume fields and SP projections are possible where entitled. The sibling did not establish durable historical movement/liquidity storage or the earliest date. No form/sectional source. | Application/account entitlement, request limits, market-data charges and historical-data package are not recorded. | **TECHNICALLY_AVAILABLE_RIGHTS_PENDING**. Historical odds, liquidity, SP retention and derived-display rights are separate gates. | Catalogue capture then pre-race book snapshots; SP is settlement evidence only and never a pre-race feature. |

Harness and greyhound remain **INSUFFICIENT_FEATURE_COVERAGE** in the audited
provider evidence. Australian horse or gallops support must not be generalized
to harness or greyhound. Greyhound box/split features and harness driver/sectional
features therefore remain unavailable for a real-data claim.

## Implemented Nexus controls

`services/api/app/external_provider_integrations.py` implements:

- provider-specific endpoint and field contracts for all four existing assets;
- a common read-only transport interface and an optional `httpx` implementation;
- server-side-only credential resolution by injection; no credential is read at
  import time, placed in source, or included in request metadata;
- `SourceApprovalRecord` checks for complete rights/retention/training/display
  evidence plus explicitly named operations and racing codes;
- bounded probe plans that describe calls and quality checks but do not execute;
- common `RawEnvelope` receipts with checksums, timestamps, rights state and
  retrieval metadata;
- Betfair catalogue/book separation and a test that does not admit starting
  price as a pre-race input;
- a default `build_disabled_provider_adapters()` registry with no transport or
  credential resolver.

The adapter does not include market orders, staking, wagering or trading
operations. The existing synthetic Betfair fixture remains the offline path.

## Verified versus unresolved evidence

Verified from the sibling implementation and sanitized records:

- endpoint paths and read-only request shapes listed above;
- PuntersEdge bounded AU thoroughbred result/form response shape;
- Krok AU thoroughbred result/form/odds response shape, with incomplete price
  evidence;
- Betfair AU catalogue/book authentication and response shape in tests and
  delayed validation;
- sibling retry, timeout, response-size, identity and fail-closed parsing
  patterns that informed the Nexus seam.

Not verified for Nexus and therefore blocked:

- earliest historical date and completeness for any provider;
- durable publication timestamps for every field;
- current plan, quota, overage and monthly cost for all accounts;
- retention/export rights, feature-engineering rights, ML training/calibration
  rights and derived forecast display rights;
- cross-provider identity reconciliation coverage;
- Betfair historical odds/liquidity depth and market-data licence scope;
- harness and greyhound coverage.

## Minimal owner approval record

For each provider/code/operation, record:

1. provider and exact operation (`LIST_MEETINGS`, `GET_RESULTS`, and so on);
2. racing code and date/venue sample boundary;
3. server-side credential owner, rotation method and quota ceiling;
4. written permission for retention, feature engineering, training, calibration,
   evaluation and derived forecast display;
5. identity reconciliation and timestamp-quality evidence;
6. data deletion/expiry rule and a kill switch owner.

The Nexus gate requires the existing six source-evidence fields plus explicit
`approved_operations` and `approved_codes`. A full source record for one
provider does not authorize another provider, operation or racing code.

## First controlled experiment

1. Owner records a PuntersEdge `GET_RESULTS`/`GET_ENTRIES` approval for
   `THOROUGHBRED` and confirms the current account quota.
2. Run the two-call bounded probe outside model training, with raw payload
   retention disabled until the record is checked.
3. Validate race/runner identity, timestamps, duplicate rows, status, dead
   heats, scratchings and pre-race eligibility.
4. Persist only approved fields as licensed envelopes with a source receipt and
   dataset hash.
5. Compare coverage against the synthetic schema; abstain for missing critical
   fields. Do not call the result a validated prediction until chronological
   real-data evaluation is complete.
6. Add FormFav fields only after an independent identity link is established;
   use Krok for enrichment and Betfair for separately approved pre-race market
   snapshots.

No live probe was executed for this report. The implementation and tests use a
fake transport only.
