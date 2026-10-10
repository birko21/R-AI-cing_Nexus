# RIL-077 owner approval pack — initial thoroughbred dataset

## Decision requested

Approve one provider-specific, server-side, read-only historical-data agreement for an initial Australian thoroughbred research sample. No approval is requested for harness or greyhound data, live wagering, order/trading operations, or automatic staking.

The agreement must name R-AI-cing Nexus, not The Long Straight, and explicitly permit retention, derived feature generation, model training, evaluation, calibrated probabilities, fair-price derivation and local display for the approved categories.

## Audited options

| Provider | Initial data categories | Rights required | Cost/quota evidence | Residual risk | Current recommendation |
|---|---|---|---|---|---|
| FormFav | Thoroughbred meetings, fields, barriers, jockey/trainer, distance, form and scratch state | Historical retention, derived/model use, display and export scope; durable identity/receipt terms | Not stated in audited evidence; do not assume free | No results, starting prices, market history or source update timestamp evidenced | Useful field enrichment, not sufficient as the first complete modelling dataset |
| PuntersEdge | Thoroughbred results, prior horse form, settled fixed Win/Place prices and returned timestamps | Written application-specific model/training, retention and derived-output rights; clarify starting-price use | Personal free-plan probe recorded 2,990 credits remaining; not transferable and not a price guarantee | Long-term export depth and commercial/model rights unresolved | Lowest operational-friction candidate for a bounded results/form request, subject to a new written licence |
| Krok Odds | Thoroughbred meetings, runner form, Win/Place market enrichment, authorised results and any authorised tote/BSP fields | Written historical retention, training, display, attribution and derived-output rights | Documentation reports A$0/50 credits/month/5 rpm free tier; observed account returned `api`; historical range is paid | Complete tote/BSP and durable historical depth were not established | Lowest documented nominal-price route, but not yet a legitimate approved route |
| Betfair Exchange | Thoroughbred catalogue, selection IDs, pre-race back/lay prices, movement snapshots, available/matched volume and separately authorised SP | Read-only market-data entitlement; historical odds/liquidity retention, display, training and SP rights | Cost and data licence absent from audited repository | Closed-market reconstruction, code coverage and rights remain unresolved | Best market-intelligence complement after a form/results dataset, not the lowest-cost first route |

## Lowest-cost legitimate route assessment

No provider is currently a legitimate approved route. The lowest documented nominal price is Krok’s reported free tier, but the audited account tier and paid historical-range requirement prevent treating it as available. The safest procurement sequence is therefore:

1. Request a written PuntersEdge quote/licence for a bounded Australian thoroughbred historical sample containing results, prior form, settled prices and timestamps, with local retention and model-use rights.
2. In parallel, request written Krok terms and a sample export quote; accept the free tier only if historical access and model rights are explicitly included.
3. Treat Betfair as a separate later market-intelligence approval, with no SP or liquidity retention until the entitlement says so.

The owner should approve the first route only if the final price is within the written budget cap and the requested rights are explicit. A free personal-use account is not sufficient.

## Proposed bounded approval

- Provider: owner selects PuntersEdge or Krok after written quote comparison.
- Code: Australian thoroughbred only.
- Data: historical meetings, races, runners, results, prior form, distance/track conditions, speed/ratings/sectionals only where supplied with trustworthy timestamps, and prices only where the licence permits.
- Retention: encrypted local raw receipts for the agreed term; derived features and model artifacts retained only as permitted; deletion and backup handling recorded.
- Model use: explicit permission for feature engineering, walk-forward training, calibration, evaluation and derived probabilities/fair prices.
- Display: local single-user display only unless broader redistribution is granted; source attribution required where applicable.
- Access: server-side scoped read-only credential; no frontend exposure; no production activation before source approval record and security review.
- Budget: owner-set maximum before purchase; no subscription or paid request is authorised by this pack.

## Approval checklist

- [ ] Exact provider/product/account and legal entity recorded.
- [ ] Price, quota, overage and cancellation terms recorded.
- [ ] Historical range and timestamp semantics demonstrated with a sample.
- [ ] Runner identity and duplicate/reconciliation behaviour verified.
- [ ] Retention, backup, deletion and export rights recorded.
- [ ] Training, derived-output and display rights explicitly granted.
- [ ] Security review approves secret storage and rotation.
- [ ] Owner approves spend and activates the named source only.
