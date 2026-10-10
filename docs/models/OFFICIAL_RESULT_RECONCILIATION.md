# Official result reconciliation

RIL-042 reconciles a personal selection only against an `OFFICIAL` or `CORRECTED` result with an official timestamp. Pending results are rejected. Result corrections are new immutable revisions linked by `correction_of`; the prior result and any prior reconciliation remain available for audit.

Outcomes are explicit: `PASS`, `WIN`, `PLACE`, `LOSS`, `SCRATCHED`, `DEAD_HEAT`, or `VOID`. Dead-heat groups and scratched entries are carried by the official result revision. The registry stores only selection/result reconciliation state; model rankings and paper financial simulations are deliberately separate.

The checked-in fixture demonstrates an official result later corrected from a win to a place without mutating the original revision. It is synthetic and offline evidence, not an official result or a performance claim.
