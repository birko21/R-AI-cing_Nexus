# The Long Straight / Betfair form-enrichment ticket pack

## Purpose

This ticket pack converts the audit of `KirkMathie/The-long-straight` into the
remaining work required for a real, read-only, pre-race racing-analysis dataset
in Nexus. The goal is richer form and race-day evidence, not settled results for
the target race and not wagering.

The tickets are intentionally ordered. A provider response is never promoted
into model features until it has passed identity reconciliation, provenance,
rights, timestamp and as-of checks.

## What The Long Straight is doing today

The reviewed application uses the following Betfair path:

1. The server reads `BETFAIR_DELAYED_APP_KEY`, `BETFAIR_USERNAME` and
   `BETFAIR_PASSWORD` from the deployment environment. The values are not sent
   to the browser.
2. It POSTs to `https://identitysso.betfair.com/api/login` with the app key and
   username/password, keeps the returned session token in process memory, and
   refreshes it once after an invalid-session response.
3. It POSTs JSON-RPC requests to
   `https://api-au.betfair.com/exchange/betting/json-rpc/v1`.
4. Its runner metadata provider calls `listMarketCatalogue` with Australian
   thoroughbred filtering, `WIN` markets, venue/date bounds and
   `marketProjection: ['EVENT', 'MARKET_START_TIME', 'RUNNER_METADATA']`.
5. It builds an HTTPS Betfair silk URL from `COLOURS_FILENAME`, caches the race
   response for about one minute, and merges a bounded projection into the
   runner detail response.

The current projection includes cloth number, form, official/adjusted rating,
days since last run, age, sex, colour, colours description, wearing, sire, dam,
jockey claim and silk image URL. It does not expose every available Betfair
metadata field, does not persist a complete canonical form record, and does not
use Betfair to supply historical runner form. The Render blueprint also declares
`RACING_PROVIDER=FIXTURE`, so Betfair is enrichment rather than the canonical
race-card source in that deployment contract.

The Long Straight therefore supplies a useful authentication and silk reference,
not a drop-in replacement for the Nexus multi-provider ingestion pipeline.

Nexus currently documents a different Betfair secret shape
(`NEXUS_PROVIDER_BETFAIR_APP_KEY` plus `NEXUS_PROVIDER_BETFAIR_SESSION_TOKEN`).
That static session-token path is the first parity risk: The Long Straight's
runtime login is more operationally robust, but it must still be tested against
the same Betfair account/app-key entitlements. The two applications' secrets
must not be copied between environments or exposed in tickets.

## Epic FE-A — Betfair access and complete runner metadata

### FE-001 — Port the proven Betfair runtime-login contract into Nexus

- **Priority:** P0
- **Status:** READY / external entitlement required
- **Depends on:** None
- **Scope:** Reconcile the Nexus Betfair adapter with The Long Straight's
  server-side login/session pattern. Use the AU endpoint, bounded HTTPS calls,
  in-memory token caching, one invalid-session refresh, redirect rejection and
  response-size/time limits. Keep app key, username, password and session token
  server-only.
- **Acceptance:**
  - Render secret names and local placeholders are documented without values.
  - No token, credential, raw response or secret appears in logs, API responses,
    fixtures, browser bundles or persisted envelopes.
  - Login, invalid-session refresh and non-retryable error paths have tests.
  - The request remains read-only and cannot call order/betting operations.
- **Evidence:** Sanitised diagnostic report, auth unit tests and secret-scan
  result.
- **Blocker:** The current Nexus hosted calls return upstream HTTP 403. The
  ticket cannot be accepted until the Betfair app key/account entitlement is
  corrected or an approved read-only key is supplied.

### FE-002 — Add a Betfair entitlement and endpoint diagnostic

- **Priority:** P0
- **Status:** BLOCKED_EXTERNAL
- **Depends on:** FE-001
- **Scope:** Add a standalone, manually invoked diagnostic that distinguishes
  login failure, invalid session, app-key restriction, account access denial,
  endpoint mismatch, empty catalogue and valid catalogue. It must report only
  aggregate status, HTTP/API error class, request operation and counts.
- **Acceptance:**
  - Tests cover `ACCESS_DENIED`/HTTP 403, invalid session, empty result and
    successful `listMarketCatalogue` cases.
  - The diagnostic can query one bounded Australian venue/date without querying
    settled results or placing orders.
  - A successful result proves at least one market and one runner with
    `RUNNER_METADATA`.
  - Credentials and raw provider payloads are excluded from the report.
- **Evidence:** Randwick and Caulfield diagnostic reports for the target date,
  or an explicit provider-blocked report.

### FE-003 — Expand the Betfair runner metadata contract

- **Priority:** P1
- **Status:** READY after FE-002
- **Depends on:** FE-001, FE-002
- **Scope:** Extend the typed projection beyond the current subset. Preserve
  nulls when Betfair does not return a field; never infer a value from the
  runner name or number. Cover, when available, cloth/alpha number, form,
  official and adjusted ratings, days since last run, weight value/unit,
  stall draw, jockey, trainer, jockey claim, wearing/gear, age, sex, colour,
  sire, dam, damsire, owner, breeding, runner status, colours description and
  silk filename/URL.
- **Acceptance:**
  - Every field has a type, source key, null semantics and observed timestamp.
  - Unknown Betfair keys are retained only inside a rights-approved bounded
    metadata object or are explicitly discarded with a reason.
  - URL construction accepts only HTTPS Betfair content hosts and rejects
    arbitrary upstream URLs.
  - Contract fixtures include missing, malformed and partially populated
    metadata.
- **Evidence:** Contract/schema diff, mapping tests and field coverage report.

### FE-004 — Persist Betfair catalogue identity and metadata provenance

- **Priority:** P1
- **Status:** READY after FE-003
- **Depends on:** FE-003, existing provider-envelope and canonical projection
  contracts
- **Scope:** Project exact Betfair market ID, selection ID, market start time,
  venue/race identity, runner metadata, silk reference, source receipt,
  observed time and rights state into the canonical/provider evidence model.
  Keep raw licensed payload handling within the existing retention policy.
- **Acceptance:**
  - Re-ingesting the same catalogue is idempotent.
  - A changed runner metadata value creates a new revision/evidence record and
    does not overwrite prior as-of history.
  - Missing market/selection identity is quarantined, not guessed.
  - The persisted model can answer: “what was known before this race cutoff?”
- **Evidence:** Migration/schema check, replay test, revision test and
  quarantine report.

### FE-005 — Reconcile Betfair selections to canonical runners

- **Priority:** P0
- **Status:** READY after FE-003
- **Depends on:** FE-003, existing canonical identity model
- **Scope:** Match Betfair selection ID and cloth number to the canonical runner,
  using normalized name only as corroborating evidence. Reconcile against Krok,
  FormFav and PuntersEdge runner identifiers where present. Reject same-number,
  same-name conflicts and reserve/scratch ambiguity.
- **Acceptance:**
  - Exact matches receive a stable mapping record with evidence fields.
  - Ambiguous or conflicting matches enter quarantine with a reason code.
  - Name-only matches cannot silently enter model features.
  - Mapping remains stable across repeated catalogue captures and late
    scratchings.
- **Evidence:** Representative target-card reconciliation report covering all
  Randwick and Caulfield races, including unmatched/conflict counts.

### FE-006 — Capture Betfair pre-race market-book evidence

- **Priority:** P1
- **Status:** READY after FE-002 and FE-005
- **Depends on:** FE-002, FE-005, existing market-quote projection
- **Scope:** After a successful catalogue capture, request bounded read-only
  `listMarketBook` data for exact market IDs. Store back/lay ladders, available
  size, matched volume, market status, in-play flag and observation time. Keep
  catalogue identity and market-book snapshots separate.
- **Acceptance:**
  - No market book is queried without a prior exact catalogue mapping.
  - Pre-race snapshots are marked by observation time and never substituted for
    historical closing prices.
  - SP, post-race and in-play values are excluded from pre-race features unless
    their timing is explicitly valid for the cutoff.
  - The existing Nexus 403 path remains fail-closed and visible as unavailable.
- **Evidence:** Market-book contract tests, exact-selection mapping report and
  bounded target-card snapshot summary.

## Epic FE-B — PuntersEdge pre-race form and card enrichment

### FE-007 — Replace target-day results probing with a pre-race form plan

- **Priority:** P0
- **Status:** READY
- **Depends on:** Existing PuntersEdge provider credentials and FE-005
- **Scope:** Add explicit PuntersEdge pre-race operations instead of using the
  settled-results operation as the target-card enrichment path. Support the
  whole-race form endpoint (`/v1/racing/form`) and full-day acceptance/card
  endpoint (`/v1/racing/acceptances`) where the account is entitled. Keep
  `/v1/racing/results` only for post-race labels and not for target-day
  pre-race features.
- **Acceptance:**
  - The planner can request the full Randwick/Caulfield target card before the
    race date without requiring a settled result.
  - Endpoint parameters use the provider's documented race/venue/date/horse
    semantics; no generic `code` parameter is sent where `horse` or race
    identity is required.
  - Results responses cannot populate a pre-race feature snapshot.
  - Every call is bounded, cached and metered against the provider credit budget.
- **Evidence:** Request-shape tests, sanitized response summaries and a target
  card pre-race run.

### FE-008 — Normalize complete PuntersEdge historical form

- **Priority:** P1
- **Status:** READY after FE-007
- **Depends on:** FE-007
- **Scope:** Normalize prior runs, Last-10, career totals, profile, track/
  distance/going splits, barrier, weight, jockey, trainer, class, field size,
  position, margin, price path, sectionals, time and gear where returned. Keep
  provider availability separate from a true zero or empty value.
- **Acceptance:**
  - Each run has source-observed and as-of timestamps where available.
  - A run after the forecast cutoff is excluded from the feature snapshot.
  - Past settled results may be used as historical form facts only when they
    were available before the target cutoff; target-race results are never used.
  - Missing sectionals, prices or profile fields remain null and are surfaced in
    coverage metrics.
- **Evidence:** Normalized fixture set, future-leak tests and field-coverage
  matrix.

### FE-009 — Implement bounded form enrichment scheduling and caching

- **Priority:** P1
- **Status:** READY after FE-007
- **Depends on:** FE-007
- **Scope:** Prefer one whole-race/full-day request over one request per horse;
  fall back to on-demand horse form only where necessary. Add request budgets,
  concurrency limits, retry classification, short-lived cache and a kill switch.
- **Acceptance:**
  - A target card cannot fan out beyond the configured request/credit budget.
  - Duplicate runner opens reuse a cached validated projection.
  - Provider outage leaves the race card usable with an explicit enrichment
    unavailable state, never synthetic form.
  - Operational status exposes counts/latency/coverage but not raw payloads.
- **Evidence:** Budget simulation, cache tests, outage test and provider health
  event.

### FE-010 — Resolve FormFav card/form contract and add it to the same pipeline

- **Priority:** P1
- **Status:** BLOCKED_EXTERNAL / contract investigation
- **Depends on:** Existing FormFav credentials and FE-005
- **Scope:** Investigate the current HTTP 422 for the documented Australian
  thoroughbred card request, confirm account entitlement and request shape, then
  normalize barriers, weights, jockeys, trainers, form and scratch state through
  the same canonical identity/provenance path.
- **Acceptance:**
  - A valid request returns one bounded target card or a precise provider
    rejection classification.
  - FormFav values are reconciled to canonical runners and never overwrite
    contradictory provider facts without a conflict record.
  - The adapter is disabled cleanly when the provider is unavailable.
- **Evidence:** Sanitized request/response diagnostics, mapping report and
  provider capability update.

## Epic FE-C — Cross-provider form dataset and model readiness

### FE-011 — Create the provider field coverage and conflict matrix

- **Priority:** P0
- **Status:** READY
- **Depends on:** FE-003, FE-007, FE-008, FE-010
- **Scope:** Define the canonical field dictionary across Betfair, PuntersEdge,
  Krok and FormFav: value type, provider key, source priority, time semantics,
  rights, null meaning, conflict rule and model eligibility.
- **Acceptance:**
  - Every model candidate feature has a declared source and fallback rule.
  - Provider disagreement is measurable and never silently averaged.
  - Fields that are display-only (for example silk artwork) are excluded from
    numeric training features unless separately justified.
  - A report distinguishes absent, unavailable, not-entitled, quarantined and
    genuinely empty values.
- **Evidence:** Versioned field matrix, conflict fixtures and coverage report.

### FE-012 — Build deterministic as-of feature materialisation

- **Priority:** P0
- **Status:** READY after FE-011
- **Depends on:** FE-004, FE-005, FE-008, FE-011
- **Scope:** Materialize runner/race features for a declared forecast cutoff.
  Include provenance and missingness for form, ratings, recency, barrier,
  weight, jockey/trainer, going, distance, class, sectionals and market context.
- **Acceptance:**
  - Replaying the same receipts and cutoff produces the same feature hash.
  - Future facts, target-race results and post-cutoff market observations are
    rejected.
  - Provider values are not replaced by synthetic defaults.
  - Features with insufficient support carry an explicit evidence/coverage flag.
- **Evidence:** Feature manifest, replay hash, leakage-injection test and
  `NOT_AVAILABLE` cases.

### FE-013 — Wire enriched features into the analysis contract without claiming
  model validity

- **Priority:** P1
- **Status:** BLOCKED until historical evaluation exists
- **Depends on:** FE-012, existing model/forecast contracts
- **Scope:** Expose the enriched evidence to the analysis service and UI while
  retaining `NOT_TRAINED`/`ILLUSTRATIVE_ONLY` states until a chronological
  historical sample, calibration and independent evaluation are complete.
- **Acceptance:**
  - The analysis response identifies feature sources, freshness, coverage and
    conflicts.
  - No probability is presented as validated merely because more fields exist.
  - The model can run in evidence-only/feature-inspection mode with no
    synthetic replacement values.
  - The no-wagering boundary remains enforced.
- **Evidence:** API contract tests, model-state tests and UI screenshot/evidence
  packet.

### FE-014 — Render enriched runner analysis with provenance and coverage

- **Priority:** P1
- **Status:** READY after FE-012
- **Depends on:** FE-012, existing frontend analysis surfaces
- **Scope:** Add complete tables/graphs for runner form, ratings, recency,
  pace/sectionals, market context and source provenance. Show Betfair silks when
  verified, but never imply that a missing silk means a missing runner.
- **Acceptance:**
  - Desktop and mobile layouts show source, observed time, freshness and
    unavailable/conflict states.
  - No synthetic cards, invented values or unlabelled provider merges appear.
  - Tables remain readable for large fields and dynamic runner counts.
  - Accessibility, keyboard focus and visual regression tests pass.
- **Evidence:** Target-card screenshots, Playwright journey and accessibility
  report.

## Epic FE-D — Real-data UAT gate

### FE-015 — Run the target-card end-to-end acceptance for 17 October 2026

- **Priority:** P0
- **Status:** BLOCKED until FE-002 and at least FE-007 pass
- **Depends on:** FE-002, FE-005, FE-007, FE-008, FE-011, FE-012, FE-014
- **Scope:** Execute the bounded pre-race workflow for Randwick and Caulfield.
  The run must ingest real provider data, reconcile the fields, materialize an
  as-of feature snapshot and render the analysis surface. It must not require
  settled target-race results.
- **Acceptance:**
  - Every returned race/runner is provider-backed or has a quarantine reason.
  - Betfair silk/metadata coverage, PuntersEdge form coverage, Krok coverage and
    FormFav status are reported separately.
  - No target-day settled result or post-race fact enters the feature snapshot.
  - The UI shows actual tables, graphs and provenance instead of a bounded
    `NOT_AVAILABLE` placeholder for the accepted fields.
  - The output remains read-only and wagering-disabled.
- **Evidence:** Sanitized release packet containing counts, coverage, conflicts,
  feature hash, model state, screenshots and command/workflow IDs.

### FE-016 — Historical sample and model-evidence gate

- **Priority:** P1
- **Status:** BLOCKED until licensed historical coverage is available
- **Depends on:** FE-012, existing walk-forward/evaluation tickets
- **Scope:** Acquire and retain a rights-approved historical sample containing
  the same pre-race fields, build chronological train/calibration/test splits,
  and evaluate uniform/form/market baselines before enabling a validated model
  state.
- **Acceptance:**
  - Historical retention and model-training rights are recorded per source.
  - No future leakage is found in the split or feature replay.
  - Metrics include log loss, Brier, calibration and coverage by code/segment.
  - Promotion remains owner-approved and cannot be triggered by data arrival
    alone.
- **Evidence:** Rights record, split manifest, evaluation report and model
  assurance checkpoint.

## Dependency order

```text
FE-001 -> FE-002 -> FE-003 -> FE-004 -> FE-005 -> FE-006
                    |                         |
                    +-> FE-007 -> FE-008 -> FE-009
                    +-> FE-010 ----------------+

FE-003 + FE-008 + FE-010 -> FE-011 -> FE-012 -> FE-013
                                           |
                                           +-> FE-014 -> FE-015
                                           +-> FE-016
```

## Explicit non-goals

- No Betfair order placement, wagering, account-balance access or trading
  automation.
- No requirement to obtain settled results for the 17 October 2026 target card.
- No use of target-race results, post-race sectionals or closing prices in a
  pre-race feature snapshot.
- No name-only silent joins across providers.
- No synthetic fallback presented as live or licensed evidence.
- No claim that a richer feature table is a validated predictive model.

## Current go/no-go summary

The reusable Betfair pattern is clear and should be ported, but Nexus is not
ready to claim complete Betfair enrichment today because its hosted catalogue
requests are still returning HTTP 403. PuntersEdge is configured for results and
on-demand horse form, but the target-card pipeline still needs explicit
pre-race form/acceptance operations. FormFav remains a separate HTTP 422
contract/account investigation. Until FE-002 and FE-007 pass, the correct
product state is real-data partial coverage with explicit unavailable fields,
not a completed enriched model.

## Ralph Loop implementation checkpoint

- **Implemented locally:** FE-001 runtime-login parity, FE-003 Betfair metadata
  whitelist/projection, FE-004 immutable provider-runner-metadata migration,
  and the PuntersEdge acceptance-card request path in FE-007.
- **Implemented locally but still requiring hosted evidence:** generic provider
  runner metadata persistence for PuntersEdge/FormFav/Krok, acceptance-card
  local-start parsing, and bounded enrichment planning.
- **Still blocked externally:** FE-002 Betfair entitlement/HTTP 403, FE-010
  FormFav HTTP 422, and FE-015 target-card UAT until at least one real
  pre-race form/card path succeeds end to end.
- **Not yet claimed:** FE-008/FE-012 complete model-ready feature
  materialisation, FE-013 validated probabilities, and FE-016 historical model
  evidence. More provider fields alone do not satisfy those gates.
