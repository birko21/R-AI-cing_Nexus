# RIL-023 probability edge-case report

Focused command: `.venv\Scripts\python.exe -m pytest services/api/tests/test_probability.py -q`

Result: `10 passed`

| Case | Expected behavior | Result |
| --- | --- | --- |
| Missing field entry | Reject exact-membership mismatch | Pass |
| Extra field entry | Reject exact-membership mismatch | Pass |
| Negative probability | Reject | Pass |
| `NaN` or infinity | Reject | Pass |
| Sum outside absolute `1e-8` | Reject | Pass |
| Zero probability with valid remainder | Accept | Pass |
| `fair_decimal_odds(0)` | Return `None`/`null`, never divide by zero | Pass |
| Observed winner with `p=0` | Return infinite natural-log loss | Pass |
| Missing winner | Reject | Pass |
| Multiclass Brier score | Use `sum((p_i-y_i)^2)` | Pass |

The validator does not repair or silently renormalize distributions. Callers must preserve the failure diagnostic and abstain.

