# PR #75 independent assurance review

## Review scope and verdict

Reviewed PR #75 at the requested commit `411a4e7494d24ca16613efd5c7b6ff41612e175e` against `origin/main` (`d36fdd5d9bfe2c541ff2c40d95c2b4d0b4227a7a`), then reviewed follow-up assurance commits `a89c163676b8a0cf77abf257486ca1a641c0eabc`, `69a6c7b7b4ab53c8760a7d201fdb9630ebc254ae`, `87642bd0dc3eef1cf4f95ebb59d6f3236e6f5f3d` and final evidence pin `ba34a0c92b151ed39b1439ea355903bc0abd646f`. The comparison contains the reported 59 changed files before the follow-ups. The PR is open, unmerged and has no recorded approval decision. The review verdict is **CONDITIONAL PASS FOR INDEPENDENT REVIEW; DO NOT MERGE UNTIL REQUIRED APPROVALS**.

The branch remains safe for synthetic-only development. It is not evidence of real-world predictive validity and must not be promoted to `MODEL_VALIDATED`.

## CI and release evidence

Latest PR workflow run: `38032679699` (10 October 2026 UTC). The four required jobs completed successfully: `backend`, `contracts-security-and-synthetic-evaluation`, `frontend` and `browser-smoke`. Duplicate push run `38032677375` also completed successfully. The recorded head, workflow and backend count are corrected in `validation-record.md`.

Local backend validation after the assurance changes: `241 passed, 1 existing Starlette/AnyIO deprecation warning`; Ruff passed. The exact commands and exit codes are retained in the validation record.

## Findings and resolutions

| ID | Severity | Finding | Resolution | Residual risk |
|---|---|---|---|---|
| PR75-001 | High | Release evidence named an earlier head (`7ef3bb2`), earlier workflow run (`38031485487`) and stale backend count (`235`). | Corrected to final follow-up head `ba34a0c`, PR run `38032679699` and the current local count. | Future changes must refresh the evidence record again. |
| PR75-002 | High | Existing evaluation reported fold labels but did not independently bind exact race membership, dataset hashes, feature snapshots and model artifacts. | Added `FoldAssuranceRecord` with exact train/calibration/test membership, cutoff/windows, dataset hash, snapshot hashes and artifact IDs. | Real historical dataset hashes and provider receipts are still unavailable. |
| PR75-003 | High | Prior “ablation” grouped already-scored cases rather than retraining challengers without a feature family. | Added `ablate_and_retrain`; tests assert a new schema and retraining callback are used. | Synthetic ablation results remain illustrative. |
| PR75-004 | High | Race-level calibration was described but not enforced as a separate held-out calibration operation. | Added deterministic race-level temperature scaling fitted only from unique calibration races. | Calibration cannot be assessed until licensed contemporaneous history exists. |
| PR75-005 | Medium | B3 row provenance did not hash the complete feature snapshot. | Training rows now hash identifiers, timestamps, values, rights mode, receipts and schema; manifests carry a sorted snapshot hash set and integrity hash. Artifact loading can require an independently trusted manifest. | The external trusted-manifest authority and retention policy are pending RIL-077. |
| PR75-006 | Medium | No independent race-level choice-model challenger existed beside runner classification. | Added a deterministic conditional-logit `ChoiceModel` with race-normalised probabilities and dedicated tests. | Challenger comparison is not a real-data result yet. |
| PR75-007 | Low | Synthetic B3 evidence could be misread as a performance claim without the explicit assurance context. | Evidence and release language now state synthetic-only, non-predictive status and no automatic promotion. | Human review remains required for future reports. |

## Assurance checks

- [x] No provider credentials, live adapter activation or external production service was introduced.
- [x] No wagering, staking, order or trading operation exists.
- [x] Betfair remains synthetic/mock only; no post-race SP is eligible as a pre-race feature.
- [x] Model artifacts fail closed on checksum, schema, data-mode and trusted-manifest mismatch.
- [x] Race probabilities are normalised by the existing contract and specialist code models remain separate.
- [x] The sibling The Long Straight repository was not modified.
- [ ] Independent human PR approval — required before merge.
- [ ] Provider-specific historical rights, retention and training permissions — required before real-data work.

## Residual release risks

The principal unresolved risks are contractual rather than implementation-only: no provider has approved R-AI-cing Nexus rights for retention, feature engineering, training, calibration, evaluation or derived forecast display; no contemporaneous historical sample has been reconciled; and no real out-of-sample accuracy or profitability evidence exists. These risks block any real-world validity claim and the RIL-077 completion gate.
