# Epic register

| Epic | Title | Gates | Priority | Depends on |
|---|---|---|---|---|
| E0 | Governance, scope and evidence | G0 | P0 | None |
| E1 | Local foundation and contracts | G1–G2 | P0 | E0 |
| E2 | Domain, provenance and entitlement controls | G1–G4 | P0 | E0, E1 |
| E3 | Synthetic data and three-code research UX | G2–G3 | P0 | E1, E2 |
| E4 | Deterministic baselines and forecast archive | G3–G5 | P0 | E2, E3 |
| E5 | Backtesting and model assurance | G5–G6 | P0 | E4 |
| E6 | Public scraping and approved provider adapters | G4, G7 | P1 | E2, E5 |
| E7 | Market workbench and paper analysis | G8 | P1 | E5, E6 |
| E8 | Selections, watchlists and responsible use | G3, G8 | P1 | E3, E4 |
| E9 | Evidence-grounded research assistant | G9 | P2 | E2, E5 |
| E10 | Specialist models and scenario studio | G10 | P2 | E2, E5 |
| E11 | Security, operations and pilot release | G11 | P0/P1 | E1–E10 |

## Epic exit criteria

- **E0:** scope, decisions, risks, traceability and checkpoint format are versioned.
- **E1:** the local application, database, contracts, authentication boundary, worker and quality checks run reproducibly.
- **E2:** canonical entities, revisions, timestamps, provenance, entitlements and quarantine behavior are testable.
- **E3:** all three codes work end-to-end in clearly labelled synthetic mode with accessible degraded states.
- **E4:** deterministic B0/B1 forecasts are coherent, immutable, replayable and honest about evidence status.
- **E5:** chronological evaluation, leakage defenses, scoring, uncertainty and champion/challenger controls are reproducible.
- **E6:** scraping and provider adapters are read-only, rate-limited, provenance-preserving and rights-gated; at least one real source passes only after approval.
- **E7:** market comparisons are timestamp-aligned, licence-aware, liquidity-aware and paper-only.
- **E8:** personal decisions, passes, outcomes, watchlists and alerts remain immutable and non-urgent.
- **E9:** the assistant can only answer from permitted, cited, as-of evidence and refuses unsupported numbers.
- **E10:** code-specific advanced features and scenarios are explicitly experimental until independently supported.
- **E11:** security, restore, observability, cost controls, deployment and owner sign-off support a restricted pilot.

