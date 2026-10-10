# Four-provider intelligence expansion backlog

## Safe work completed in this increment

| ID | Item | State | Evidence |
|---|---|---|---|
| RIL-061 | Audit the four-provider implementations, contracts, tests and validation reports from The Long Straight. | DONE | `docs/provider/FOUR_PROVIDER_CAPABILITY_MATRIX.md` |
| RIL-062 | Add the four-provider capability matrix and licensing gap report. | DONE | `docs/provider/FOUR_PROVIDER_CAPABILITY_MATRIX.md`, `docs/provider/SOURCE_LICENSING_GAP_REPORT.md` |
| RIL-063 | Define revised provider-neutral architecture with Betfair as a first-class market source. | DONE | `docs/architecture/FOUR_PROVIDER_INTELLIGENCE_ARCHITECTURE.md` |
| RIL-064 | Define independent three-code form-only, market-only and combined feature catalogue and evaluation contract. | DONE | `docs/models/FOUR_PROVIDER_FEATURE_CATALOGUE.md` |
| RIL-065 | Implement synthetic Betfair catalogue/book/runner/price-history/SP fixture through the existing rights-aware adapter contract. | DONE | `services/api/app/betfair_mock.py`, `services/api/tests/test_betfair_mock.py` |

## Next safe implementation

| ID | Item | Acceptance |
|---|---|---|
| RIL-066 | Add provider-evidence records to the capability registry. | Matrix values are typed, versioned, source-linked and cannot enable a provider by themselves. |
| RIL-067 | Add Betfair synthetic fixture generation and replay manifest. | Deterministic fixture checksum, catalogue-to-book runner joins, price movement replay, liquidity fields and SP leakage tests pass offline. |
| RIL-068 | Extend as-of feature materialization to provider observations. | Both source and retrieval timestamps precede cutoff; duplicates, unknown timestamps and unapproved rights quarantine. |
| RIL-069 | Build independent code-specialist model scaffolds. | Separate thoroughbred, harness and greyhound schemas/models; form-only, market-only and combined variants; all initially `ILLUSTRATIVE_NOT_VALIDATED`. |
| RIL-070 | Add feature/provider ablation reports. | Walk-forward evaluation compares baseline and one incremental family/provider with log loss, Brier, calibration, coverage and uncertainty. |
| RIL-071 | Add independent model assurance workflow. | Leakage audit, split-manifest review, calibration review and manual registry decision are required before any promotion. |

## Blocked external work

| ID | Item | Blocker |
|---|---|---|
| RIL-072 | Implement FormFav live adapter. | Provider-specific access, retention, display and model-use approval; only gallops coverage evidenced. |
| RIL-073 | Implement PuntersEdge live adapters. | Provider-specific approval for this application, historical retention and model-use rights; personal-use evidence does not transfer. |
| RIL-074 | Implement Krok live adapters. | Resolve API/free tier, complete historical/dividend evidence and written model/retention rights. |
| RIL-075 | Implement Betfair read-only adapter. | Explicit read-only credentials, market-data/historical licence, cost approval, liquidity/SP retention and model-use rights. |
| RIL-076 | Enable any external provider in runtime. | All source approval gates, security review, budget and manual fallback evidence must pass. |

Trading endpoints, automated staking, wagering, order placement and unapproved external connectivity are not backlog items.
