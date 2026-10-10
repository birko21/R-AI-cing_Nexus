# Paper-only value and settlement simulation

RIL-039 models hypothetical scenarios in an append-only paper ledger. It records requested and matched stake, liquidity-limited fill status, fees, commission, exposure, settlement outcome, removal factor, dead-heat places, and net scenario result.

The simulator handles `WIN`, `LOSS`, `VOID`, `DEAD_HEAT`, and `SCRATCHED`. Scratchings produce no fill; missing or zero liquidity produces an explicit unfilled state; partial liquidity and fill ratio are retained as assumptions. Commission applies to positive scenario profit, fees apply to matched stake, dead heats divide profit by declared places, and removal factors reduce positive gross profit.

Exposure is bounded by an explicit maximum and positions/settlements are append-only. Results carry `guaranteed: false` and the fixture carries `paper_only: true`. This module has no network client, credential handling, order endpoint, bookmaker integration, staking action, or claim of guaranteed/profitable returns.
