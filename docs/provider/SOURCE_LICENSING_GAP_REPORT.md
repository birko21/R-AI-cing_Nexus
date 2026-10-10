# Source licensing gap report

## Current decision

All four external providers are **BLOCKED_EXTERNAL** for R-AI-cing Nexus. The sibling application’s credentials, permissions, personal-use decisions and deployment context do not transfer. The only enabled Betfair surface is the offline synthetic fixture.

## Required evidence per provider

Before activation, the source approval record must identify the exact account/product and retain evidence for:

- access authorization and credential ownership;
- permitted racing codes, endpoints and request modes;
- cost, quota and material-spend ceiling;
- retention duration, backups, export and deletion obligations;
- display/attribution rights;
- historical odds and starting-price rights, if used;
- explicit predictive-model/training/evaluation rights;
- redistribution and multi-user restrictions;
- provider security requirements and secret rotation owner;
- representative reconciliation and source-health results.

## Provider gaps

| Provider | Evidence currently present | Blocking gaps | Safe next action |
|---|---|---|---|
| FormFav | Sibling code proves a bounded Australian gallops catalogue parser and server-only key shape. | No R-AI-cing authorization; cost, retention, display, redistribution and model-use terms not recorded; no harness/greyhound evidence. | Obtain written terms for the exact private research use, then run a low-volume reconciliation without storing raw credentials. |
| PuntersEdge | Sibling report records personal-use approval, a bounded free-plan probe and fixed-price result semantics. | No approval for this application; no multi-user/redistribution/model-use/retention record; historical depth and quota sustainability remain unproven. | Obtain a provider-specific licence/terms record and a historical sample plan before any adapter is enabled. |
| Krok Odds | Sibling report records documented endpoint shapes, terms summary and fail-closed live probes. | API tier rather than free tier observed; no complete tote/BSP evidence; historical depth, retention, display and model-use scope unresolved. | Resolve account tier and written data/model rights; do not treat finishing-order evidence as settlement or training approval. |
| Betfair Exchange | Sibling code proves a read-only authentication/test shape, catalogue runner IDs and delayed SP validation. | No R-AI-cing credentials or permission; market-data/API costs, historical odds access, liquidity retention, display, SP and model-training rights unresolved; no code-specialist coverage proof. | Obtain explicit read-only market-data authorization and historical-data licence terms. Implement only against synthetic/mock contracts until approved. |

## Activation gates

An external adapter cannot be activated merely because an environment variable exists. The following must all be true for the named provider and named operation:

1. `SourceApprovalRecord` is complete and independently reviewed.
2. Cost/quota limits are recorded and within the owner-approved budget.
3. Credentials are server-side, scoped read-only and absent from fixtures/logs/frontend.
4. Raw receipts, retention and deletion behaviour match the licence.
5. Historical timestamps and exact runner joins pass representative reconciliation.
6. Model use is explicitly permitted before any provider field enters training/evaluation.
7. A kill switch, outage handling and manual fallback are tested.

Until then the provider remains `UNASSESSED`/disabled and its data cannot influence canonical state, forecasts, evaluation claims or user-facing market display.
