# Decision register

**Scope:** v1.1 offline MVP and later-gate constraints  
**Owner:** Product owner  
**Last reviewed:** 10 October 2026

Statuses: `DECIDED_BY_SPEC`, `OPEN_OWNER`, `BLOCKED_EXTERNAL`, `DEFERRED`.

| ID | Decision | Status | Default/control | Owner action |
|---|---|---|---|---|
| D-001 | Active delivery scope | DECIDED_BY_SPEC | G0–G3 offline MVP only; later vision remains backlog | None |
| D-002 | Repository | DECIDED_BY_SPEC | Use `birko21/R-AI-cing_Nexus`; no second remote | None |
| D-003 | Data mode for G0–G3 | DECIDED_BY_SPEC | Synthetic-only, visibly labelled; no real predictive claim | None |
| D-004 | External connectivity for G0–G3 | DECIDED_BY_SPEC | Disabled; controlled scraping is deferred to a later gate | None |
| D-005 | Wagering boundary | DECIDED_BY_SPEC | No bookmaker credentials, order API, staking or hidden execution path | None |
| D-006 | Local architecture | DECIDED_BY_SPEC | React/Vite + FastAPI + local PostgreSQL; modular monolith | None |
| D-007 | Local authentication | DECIDED_BY_SPEC | Loopback development token only with explicit environment flags; fail closed otherwise | None |
| D-008 | Production authentication | DEFERRED | Approved OIDC is a later gate; no production/public deployment in MVP | Owner approval before G11 |
| D-009 | Baseline models | DECIDED_BY_SPEC | Deterministic B0 uniform and code-aware B1 illustrative heuristic | None |
| D-010 | Model status | DECIDED_BY_SPEC | G0–G3 models are never `MODEL_VALIDATED` | None |
| D-011 | Provider and market data | BLOCKED_EXTERNAL | No provider, paid feed or live odds source approved | Written rights and credentials required |
| D-012 | Public scraping | DECIDED_BY_SPEC | Permitted only as controlled, public, rate-limited, provenance-preserving later work; no access-control bypass | Reconfirm source-by-source before adapter |
| D-013 | Third-party LLM data transfer | DECIDED_BY_SPEC | Disabled until rights, privacy and cost approval | Owner approval before G9 |
| D-014 | Cloud hosting and spend | DECIDED_BY_SPEC | No paid cloud or public deployment in G0–G3 | Budget approval before G11 |
| D-015 | Missing contractual artifacts | OPEN_OWNER | Create active MVP contracts from v1.1 requirements and record them as authored artifacts | Review before G1 claims |
| D-016 | Time and fixture date | DECIDED_BY_SPEC | Persist UTC; display Australia/Sydney; fixture date is fictional and selectable/time-shiftable | None |
| D-017 | Dead heats and coupled entries | DECIDED_BY_SPEC | Exclude ties from primary scoring; abstain on coupled groups | None |
| D-018 | Unknown timing proof | DECIDED_BY_SPEC | Missing verifiable publication/receipt proof is excluded from point-in-time inputs | None |
| D-019 | Correction semantics | DECIDED_BY_SPEC | Append revisions; forecasts and selections are write-once; outcomes may receive addenda | None |
| D-020 | Release approval | DECIDED_BY_SPEC | Gates require observed evidence; no automatic model promotion | Owner signs restricted pilot |
| D-021 | Four-provider intelligence expansion | BLOCKED_EXTERNAL | FormFav, PuntersEdge, Krok Odds and Betfair Exchange are separate candidates; Betfair is first-class market intelligence, but all real adapters remain disabled | Provider-specific access, cost, retention, display and model-use evidence |
| D-022 | Synthetic Betfair development | DECIDED_BY_SPEC | Offline catalogue/book/runner/price-history/SP fixture may progress contracts and tests; no credentials, login, trading, staking or external connectivity | None |
| D-023 | Specialist model promotion | DECIDED_BY_SPEC | Thoroughbred, harness and greyhound form-only/market-only/combined inputs remain illustrative until walk-forward evaluation, calibration and independent assurance pass | Owner approval after evidence review |
| D-024 | RIL-061 historical modelling foundation | DECIDED_BY_SPEC | Shared feature provenance, strict as-of eligibility, explicit exclusions, pinned LightGBM/CatBoost B3 contracts and synthetic-only evidence may progress offline; provider rights are not assumed | Resolve RIL-077 before real historical modelling |

## Open decisions requiring owner attention

No owner response is required for current G0 work. The following remain explicit future gates: approval of any real provider or scraper source, production OIDC, cloud spend, external LLM transfer, retention terms, and promotion of any model beyond illustrative status.
