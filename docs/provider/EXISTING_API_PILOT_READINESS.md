# Existing API pilot readiness — RIL-061

Status: **PILOT PREPARED; LIVE REQUESTS BLOCKED**  
PR: [#75](https://github.com/birko21/R-AI-cing_Nexus/pull/75)  
Required head: `af7aea932e3768990c3ba3b23b241983a4148ff7`

This is an activation-readiness record, not a vendor-procurement proposal.
The audit used the sanitized templates and reports in the read-only audit
checkout of `KirkMathie/The-long-straight` at commit
`3ce0da06605e01d93d48398dc8ed471aa5c294f3`. No production secret, raw provider
payload or sibling-repository change was used.

## PR and CI evidence

- Local commit `af7aea932e3768990c3ba3b23b241983a4148ff7` was a fast-forward
  child of the PR branch at `d9f924924d3be608ef9439ece3001432e91dfead`.
- The commit was pushed without force-push to
  `feature/ril-061-real-data-readiness`.
- Both push and pull-request workflow runs passed all four jobs: backend;
  contracts/security/synthetic evaluation; frontend; browser smoke.
- The independent reviewer request is open for `birko21`. No review has been
  recorded. PR #75 remains unmerged.
- No branch protection bypass, merge or deployment was performed.

## Entitlement assessment

| Provider | Read-only account/API evidence | Local retention and historical analysis | ML training | Derived forecast display | Current decision |
|---|---|---|---|---|---|
| PuntersEdge | **Verified in sibling evidence**: personal free plan, key created 2026-09-24, sanitized final AU thoroughbred response, 2,990 credits remaining after the bounded sample. | Personal-use result polling is documented. Nexus retention and historical research rights are not separately recorded. | **Unresolved for Nexus.** Personal deployment approval is not a training licence. | **Unresolved for Nexus.** Existing source semantics are settled fixed Win/Place, not tote. | Best first candidate; named Nexus operation approval required. |
| FormFav | **Technically evidenced**: server-only key pattern and AU gallops card adapter. Owner confirms existing account/API access. | Private single-user non-commercial use is documented in the sibling; Nexus retention and historical export depth are not evidenced. | **Unresolved.** No training permission found. | **Unresolved for Nexus.** | Field/catalogue pilot only after named approval. |
| Krok Odds | **Verified in sibling evidence**: owner-authorised server context returned HTTP 200 and `api` tier for read-only probes. | Terms/evidence describe private internal use and attribution; historical range is a paid-feature concern and retention is not recorded for Nexus. | **Unresolved.** Intended-use review and non-transferable key restrictions apply. | **Conditionally described** for private tools with attribution; Nexus approval remains absent. | Enrichment/results remain blocked pending rights and complete-field evidence. |
| Betfair Exchange | **Technically evidenced**: read-only login/catalogue/book shapes and AU horse event type 7. Current account package/market-data entitlement is not recorded in Nexus evidence. | Historical odds/liquidity depth, storage and export rights are unresolved. | **Unresolved.** | **Unresolved.** | Separate pre-race market pilot only after explicit entitlement approval. |

The sibling’s account configuration is not copied. Its `.env.example` confirms
only the intended server-side credential pattern and disabled/default modes.
No actual `.env` file or secret was read. The Long Straight remains unchanged.

## PuntersEdge probe plan

The first probe is opt-in and must be approved as the exact operation
`punters-edge:THOROUGHBRED:{operation}` before a transport is supplied to the
Nexus adapter. It is deliberately small enough for the observed free-plan
credit balance and has a hard ceiling of **six HTTP requests per run**:

| # | Operation | Request shape | Purpose |
|---:|---|---|---|
| 1 | `GET /v1/keys/info` | account metadata only | Plan, key status, quota/credits and documented entitlement. Do not retain the key or response body. |
| 2 | `GET /v1/racing/results` | `date=2026-09-19`, `categories=horse`, `country=AU`, `venue=Randwick` | Reproduce the previously sanitized positive sample and inspect race/runner fields, statuses, fixed prices and timestamps. |
| 3 | `GET /v1/racing/results` | owner-approved earlier or boundary date, same category/country and one venue | Establish whether historical coverage extends beyond the known sample. The date must be recorded before execution; no open-ended date search is permitted. |
| 4–6 | `GET /v1/racing/horses/form` | `runner_ref` for at most three runners returned by request 2; `limit=6` | Inspect prior form, distance, speed/sectional fields, timestamps and historical row depth. |

Expected maximum: 1 account request + 2 result requests + 3 form requests = 6.
No pagination, retries or automatic date expansion are allowed in the first
run. A timeout or schema failure consumes the attempt and returns an explicit
unavailable state; it does not trigger unbounded retrying.

### Required operational log

Only sanitized metadata may be logged: run ID, provider, operation, code,
date/venue hash, request ordinal, HTTP status class, row count, response byte
count, elapsed milliseconds, quota observation and parser outcome. Never log
API keys, authorization headers, raw URLs containing secrets, raw payloads,
runner names or provider error bodies.

### Validation rules

The probe must check:

- exact race and runner identifiers, duplicate rows and same-provider identity
  conflicts;
- final/interim/abandoned/no-result status and dead-heat representation;
- `start_time`, `resulted_at`, form `fetched_at` and any provider publication
  timestamp, without treating retrieval time as publication time;
- whether speed, sectional, distance, track-condition, barrier, jockey and
  trainer fields are actually returned;
- pre-race eligibility and exclusion of settled prices/results from features;
- completeness by race and runner, with no silent imputation of critical data;
- the provider’s observed quota/credit delta and response-size limits.

The probe may produce an in-memory validation summary. It may not persist raw
historical data, train a model or display derived forecasts until the approval
record confirms retention, feature engineering, training, calibration,
evaluation and derived-display rights.

## Remaining approvals

Before execution, the owner must record:

1. PuntersEdge source ID and the exact six-request operation/code allowlist;
2. current account plan, quota and credit-cost confirmation;
3. written permission applicable to Nexus for local retention and historical
   analysis;
4. explicit ML training, calibration, evaluation and derived-display rights;
5. approved historical date boundary and one venue sample;
6. server-side credential owner/rotation and a quota kill switch.

The Nexus gate already requires complete source evidence plus explicit
`approved_operations` and `approved_codes`. Until these fields are supplied,
`build_disabled_provider_adapters()` has no transport and cannot make a
provider request.

## Next modelling gate

When genuine contemporaneous historical data is authorised, build a separate
thoroughbred experiment with form-only, market-only and combined models. Use
race-level chronological train/calibration/test splits, walk-forward folds,
feature-family ablations, calibration assessment and independent assurance.
The first dataset report must distinguish:

- provider observation/publication time from retrieval time;
- pre-race prices from post-race starting prices and results;
- settled fixed prices from exchange prices and liquidity;
- complete, incomplete, scratched, abandoned, dead-heat and ambiguous races.

Synthetic results remain illustrative and cannot promote a model or establish
real-world predictive performance.
