# RIL-077 provider decision package

## Decision status

No provider is approved or enabled. This package is an owner-review and vendor-enquiry preparation artifact based on sanitized The Long Straight evidence. It does not authorize a subscription, paid request, credential activation, raw-data retention or model training.

### Evidence-backed comparison

| Provider / exact product evidenced | Australian code evidence | Historical and performance fields | Prices / movements / liquidity | Earliest date and timestamps | Identity and quality | Rights and cost position |
|---|---|---|---|---|---|---|
| PuntersEdge Racing API: `/v1/racing/results` and `/v1/racing/horses/form` | Thoroughbred only in audited probes; harness/greyhound not established | Results, positions, dead heats, horse form, track/date, career/profile fields, returned starting prices and settled fixed Win/Place prices | Fixed-price fields evidenced; exchange movement/liquidity not evidenced | Earliest available date is **not evidenced**. `start_time`, `resulted_at`, `fetched_at` parsed where returned | Fail-closed matching; incomplete/interim/ambiguous results excluded; durable provider IDs/export depth need confirmation | Personal free-plan probe only; 2,990 credits after probe. Application-specific retention, training, derived-output and display rights missing. Expected monthly cost: **quote required; no spend approved**. |
| Krok Odds Racing API: `/api/v1/racing/odds`, `/meetings`, `/runner-form`, results/tote probes | Thoroughbred result validation only; other codes not established | Runner form, recent placings, Win/Place market enrichment, source class; complete ratings/sectionals not evidenced | Win/Place enrichment; complete historical movement, tote/BSP and liquidity not established | Earliest available date is **not evidenced**; `meta.timestamp` parsed; historical range reportedly paid | Bounded validation and race-identity checks; observed account returned `api`, not proof of free tier | Reported free tier A$0/50 credits/month/5 rpm, historical range paid. Retention, ML, derived forecasts and display rights missing. Expected monthly cost: **quote required**. |
| FormFav Form API: `/v1/form/meetings` and `/v1/form` | Australian gallops/thoroughbred only; harness/greyhound not evidenced | Meetings, venue, race/time/distance, runner, barrier, jockey, trainer, weight, form, scratch flag; no results/ratings/sectionals evidenced | No market, price movement or liquidity endpoint evidenced | Earliest available date is **not evidenced**; race `startTime` parsed, source update timestamp unavailable | Bounded parser but durable upstream meeting/race/runner IDs absent | Sibling context is private single-user non-commercial; no R-AI-cing retention/training/display rights. Cost: **not stated; quote required**. |
| Betfair Exchange API-NG / market data: `listMarketCatalogue`, `listMarketBook` | Australian horse-racing event type 7 and WIN/PLACE only evidenced; harness/greyhound not established | Catalogue market/runner identity and start; read-only book prices, `SP_AVAILABLE`/`SP_TRADED` shape; full historical form/speed/sectionals are not provider fields | Pre-race back/lay snapshots are design targets; available back/lay volume and matched volume require authorised capture; historical odds depth and movement series not evidenced; SP is separate and post-race unless entitlement permits | Earliest historical date is **not evidenced**. `marketStartTime` and retrieval timestamps available in design; contemporaneous pre-race capture required | Selection IDs are strong join candidates; venue/race name parsing needs reconciliation; closed-market/SP reconstruction not established | No R-AI-cing credentials, market-data licence, historical retention, liquidity/SP, training or display rights. Cost/API quota: **quote and entitlement review required**. |

## Proposed approval decisions and budget

1. Approve vendor enquiries only, at A$0 spend.
2. Set a provisional owner budget ceiling of **A$250/month** for a bounded Australian thoroughbred research sample, subject to written quote and approval. This is a planning ceiling, not authorization to spend.
3. Prefer a comparison between PuntersEdge and Krok for the first form/results sample. Accept neither until the licence explicitly covers raw retention, feature engineering, training, held-out calibration, evaluation, derived fair prices and local display.
4. Treat FormFav as optional catalogue/field enrichment, not a complete training dataset.
5. Defer Betfair until a separate read-only market-data decision covers pre-race prices, movement snapshots, available/matched volume, historical retention and SP restrictions.
6. Do not generalize thoroughbred approval to harness or greyhound.

## Minimum sample request

Request 24 consecutive months of Australian thoroughbred data, targeting at least 10,000 completed races where available, with all runners, scratchings, abandoned-race markers, race/runner IDs, scheduled starts, publication/observation/retrieval timestamps, distance, track condition, venue, class, barrier, participants, results and any licensed speed/sectional/price fields. Ask the vendor to state the true earliest available date and whether timestamps are source publication time or retrieval time.

## Vendor-enquiry drafts — do not send without owner authorization

### PuntersEdge draft

> Please quote an export or API package for R-AI-cing Nexus covering 24 consecutive months of Australian thoroughbred meetings, races, runners, results, prior horse form, distance/track context and settled fixed Win/Place or starting-price fields where available. Please state the earliest available date, field dictionary, stable identity fields, timestamp semantics, quotas, overage pricing and expected monthly cost. We require written permission for encrypted local raw retention, derived feature generation, temporal training, held-out calibration/evaluation, derived probability/fair-price display and deletion/export handling. The permission must name R-AI-cing Nexus and must not rely on a personal-use permission from another application.

### Krok Odds draft

> Please confirm the exact Krok Odds product/tier available to R-AI-cing Nexus for a bounded 24-month Australian thoroughbred historical sample. Please identify earliest date, results/form/odds/tote/BSP/sectional fields, source classification, publication/observation timestamps, stable race/runner IDs, request quotas, historical-range limits, credits, overages and monthly cost. Please state whether raw retention, feature engineering, model training, calibration, evaluation, derived forecasts/fair prices and local display are permitted, and for how long. Please distinguish bookmaker prices, tote dividends, exchange prices and liquidity fields.

### FormFav draft

> Please confirm whether the FormFav Form API product may be used by R-AI-cing Nexus for Australian thoroughbred historical field/catalogue enrichment. Please provide earliest date, meeting/race/runner identity guarantees, barrier, participant, distance, track-condition and form fields, source update/publication timestamps, quota, price and overage terms. We require written rights for local retention, derived features, model training/evaluation, forecast display and deletion. Please state whether results, starting prices, speed, sectionals or any market data are available; if not, confirm that the product is catalogue-only.

### Betfair draft

> Please provide the exact read-only Betfair Exchange market-data product and licence available to R-AI-cing Nexus for Australian racing. We need Australian thoroughbred market catalogue and runner selection IDs, contemporaneous pre-race back/lay prices, available-to-back/lay volume, matched volume, timestamped movement snapshots and any separately licensed historical odds/SP data. Please state earliest available date, event-type/code coverage, API request limits, charges, data retention, derived feature/model training, calibration/evaluation and local display rights. No order placement, trading, staking or wagering operation is requested.

## Licensing checklist

- [ ] Contract names R-AI-cing Nexus and the legal/account owner.
- [ ] Exact product, endpoints, codes, earliest date and sample fields identified.
- [ ] Publication, observation, retrieval and race-start timestamp semantics demonstrated.
- [ ] Stable race/runner identity namespace and reconciliation rules documented.
- [ ] Raw retention, backup, export and deletion term approved.
- [ ] Feature engineering and derived dataset rights approved.
- [ ] Training, calibration, evaluation and model-artifact retention rights approved.
- [ ] Derived probability/fair-price display and attribution rights approved.
- [ ] Prices, SP, movement and liquidity rights separately approved where used.
- [ ] Quotas, overages, monthly cost and cancellation terms recorded.
- [ ] Server-side secret handling, rotation and kill switch reviewed.
- [ ] Owner approves spend and explicitly activates only the named provider/code.
