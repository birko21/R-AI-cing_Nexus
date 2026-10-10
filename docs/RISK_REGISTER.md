# Risk register

| ID | Risk | Severity | Trigger | Mitigation/control | Owner |
|---|---|---|---|---|---|
| R-001 | Future information leaks into forecasts | Critical | Feature known after cutoff or result correction changes replay | Bitemporal timestamps, cutoff query tests, frozen manifests and fail-closed abstention | Engineering |
| R-002 | Synthetic data is mistaken for real evidence | Critical | Missing watermark or real-performance language | `SYNTHETIC_ONLY` mode, UI banners, report wording and no validation status | Product |
| R-003 | Wagering capability is introduced accidentally | Critical | Order route, bookmaker secret, staking action or external betting call | Static scans, route allowlist, no-order tests and permanent scope rule | Engineering |
| R-004 | Repository contract is incomplete or contradictory | High | Missing v1.1 supporting artifact or conflicting requirement | Source manifest, decision register, traceability and ADR review | Product/Engineering |
| R-005 | Runner/entry identity collision | Critical | Name-only match or unresolved market mapping | Canonical IDs, quarantine, source linkage and mapping tests | Data |
| R-006 | Forecast archive is mutated | Critical | Result correction or scratching edits old forecast | Append-only revisions, write-once constraints and immutability tests | Data |
| R-007 | Local auth bypass is exposed externally | Critical | Non-loopback bind with dev token enabled | Startup fail-closed checks and bind-mode security tests | Security |
| R-008 | Provider or scraper rights are misinterpreted | Critical | Unclear terms, restricted storage/export or access-control bypass | Entitlement registry, source kill switch, no bypass policy and approval gate | Owner |
| R-009 | Public scraper is blocked or changes schema | High | 403/429/CAPTCHA/parser drift or robots restriction | Rate limits, parser versioning, quarantine, health monitoring and disable switch | Data |
| R-010 | Model quality is overstated | High | Synthetic score described as validated or profitable | Illustrative status, proper metrics, sample labels and human promotion approval | Quant |
| R-011 | Duplicate ingestion creates duplicate forecasts/alerts | High | Retry or replay repeats source event | Idempotency keys, checksums and replay tests | Data |
| R-012 | Local database is not disposable or recoverable | High | Migration targets wrong DB or restore fails | Safety guard, isolated DB, backup/restore smoke and migration evidence | Operations |
| R-013 | Data or secrets reach an external service | Critical | Provider payload or token appears in LLM/log/frontend | Server-side secrets, redaction, egress controls and secret scanning | Security |
| R-014 | Scope expands before the MVP is proven | Medium/High | Live feeds, AI, scenarios or cloud work enters G0–G3 | Stop line, dependency labels and gate checkpoints | Product |
| R-015 | Accessibility or stale-state UI misleads users | High | Status is colour-only, stale data appears current or keyboard path fails | Explicit status text, timestamps, responsive E2E and accessibility tests | UX |
| R-016 | Costs exceed local-only assumptions | Medium | Unbounded API/model calls or unexpected hosted resource | Default no-egress, budgets, quotas, kill switches and owner approval | Operations |

## Risk review rule

Critical risks block a gate. High risks require a recorded mitigation or explicit owner acceptance. A green-looking UI or passing unit test cannot override an unresolved rights, auth, leakage, provenance or wagering risk.

