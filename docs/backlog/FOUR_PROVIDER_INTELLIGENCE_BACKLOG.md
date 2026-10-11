# Four-provider intelligence expansion backlog

## Safe work completed in this increment

| ID | Item | State | Evidence |
|---|---|---|---|
| RIL-061 | Audit the four-provider implementations, contracts, tests and validation reports from The Long Straight; establish the historical modelling foundation. | PARTIAL_SAFE_FOUNDATION | `docs/evidence/ril-061/release-gate-checklist.md`, `docs/provider/FOUR_PROVIDER_CAPABILITY_MATRIX.md` |
| RIL-062 | Add the four-provider capability matrix and licensing gap report. | DONE | `docs/provider/FOUR_PROVIDER_CAPABILITY_MATRIX.md`, `docs/provider/SOURCE_LICENSING_GAP_REPORT.md` |
| RIL-063 | Define revised provider-neutral architecture with Betfair as a first-class market source. | DONE | `docs/architecture/FOUR_PROVIDER_INTELLIGENCE_ARCHITECTURE.md` |
| RIL-064 | Define independent three-code form-only, market-only and combined feature catalogue and evaluation contract. | DONE | `docs/models/FOUR_PROVIDER_FEATURE_CATALOGUE.md` |
| RIL-065 | Implement synthetic Betfair catalogue/book/runner/price-history/SP fixture through the existing rights-aware adapter contract. | DONE | `services/api/app/betfair_mock.py`, `services/api/tests/test_betfair_mock.py` |
| RIL-066 | Add typed provider-evidence records to the capability registry without granting activation authority. | DONE | `services/api/app/provider_evidence.py`, `fixtures/synthetic/provider_evidence_v1.json`, `services/api/tests/test_provider_evidence.py` |
| RIL-067 | Add Betfair synthetic fixture generation, replay manifest and drift reconciliation. | DONE | `scripts/generate_betfair_replay_manifest.py`, `fixtures/synthetic/betfair_market_replay_manifest_v1.json`, `services/api/tests/test_betfair_mock.py` |
| RIL-068 | Extend as-of feature materialization to provider observations. | SAFE_FOUNDATION | `services/api/app/provider_feature_bridge.py`, `services/api/tests/test_provider_feature_bridge.py`; provider rows with unknown timestamps, missing retention, unapproved rights or post-cutoff timing are quarantined before materialization. |
| RIL-069 | Build independent code-specialist model scaffolds and nine-lane manifest. | SAFE_FOUNDATION | `services/api/app/specialist_models.py`, `fixtures/synthetic/specialist_models_v1.json`, `services/api/tests/test_specialist_models.py` |
| RIL-070 | Add deterministic feature/provider ablation report. | SAFE_FOUNDATION | `services/api/app/ablation.py`, `fixtures/synthetic/ablation_v1.json`, `services/api/tests/test_ablation.py`; same-holdout metrics, coverage, uncertainty, hash and HOLD promotion status are verified offline. |
| RIL-071 | Add independent model-assurance workflow contract. | SAFE_FOUNDATION | `services/api/app/assurance.py`, `fixtures/synthetic/assurance_packet_v1.json`, `services/api/tests/test_assurance.py`; leakage, split and calibration checks remain HOLD until independent and owner references exist. |

## RIL-061 implementation evidence

The common `historical-features-v1` contract, B0–B4 offline benchmark interfaces, synthetic walk-forward evaluation report, deterministic forecast explanations and provider/code readiness verdicts are implemented. All generated results are `ILLUSTRATIVE_SYNTHETIC_ONLY`; B3 is explicitly unavailable until an approved LightGBM or CatBoost dependency is selected. Real provider credentials, external connectivity, wagering and trading remain disabled.

## Next development gate

| ID | Item | Acceptance |
|---|---|---|
| RIL-077 | Approve a historical dataset for real walk-forward research. | Provider-specific rights permit retention, derived features, training and derived outputs; contemporaneous timestamps and identity evidence are sufficient; the pinned LightGBM/CatBoost dependency decision is already recorded; no model promotion occurs automatically. |

## Next safe implementation

| ID | Item | Acceptance |
|---|---|---|
| T-C / RIL-060 | Aggregate release evidence into a fail-closed gate. | Synthetic local evidence, automated checks, owner review, external dependencies and prohibited capabilities are represented in one hashed report with no activation or promotion authority. |
| T-A / G1 | Execute disposable PostgreSQL apply/rollback/verify smoke. | The guarded `pnpm db:smoke` harness validates a loopback/disposable target, then verifies migration checksums, ingestion schema and upgrade/downgrade/re-upgrade behavior when a user-supplied `DATABASE_URL` is available. |
| T-A / RIL-068 | Broaden provider as-of reconciliation coverage. | Timestamp, retention, rights and cutoff edge cases remain quarantined before historical materialization; no real provider rows are required. |

RIL-069–071 now have safe synthetic foundations in this branch. Their remaining
acceptance is independent review and owner/model decision evidence; they cannot
be promoted by CI. No additional provider-specific adapter work is safe until
the RIL-072–077 rights and dataset gates below are satisfied.

## Blocked external work

| ID | Item | Blocker |
|---|---|---|
| RIL-072 | Implement FormFav live adapter. | Provider-specific access, retention, display and model-use approval; only gallops coverage evidenced. |
| RIL-073 | Implement PuntersEdge live adapters. | Provider-specific approval for this application, historical retention and model-use rights; personal-use evidence does not transfer. |
| RIL-074 | Implement Krok live adapters. | Resolve API/free tier, complete historical/dividend evidence and written model/retention rights. |
| RIL-075 | Implement Betfair read-only adapter. | Explicit read-only credentials, market-data/historical licence, cost approval, liquidity/SP retention and model-use rights. |
| RIL-076 | Enable any external provider in runtime. | All source approval gates, security review, budget and manual fallback evidence must pass. |

Trading endpoints, automated staking, wagering, order placement and unapproved external connectivity are not backlog items.
