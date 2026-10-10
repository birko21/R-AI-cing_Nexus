# Probability validation and scoring conventions

RIL-023 validates every forecast before scoring or transforming it:

- field membership is exact: every and only every field entry ID must have one probability;
- probabilities must be finite and non-negative;
- absolute normalization error must be at most `1e-8`;
- `0.0` is a valid probability, but a distribution whose observed winner has `p=0` receives infinite natural-log loss;
- fair decimal odds are `1 / p` for `p > 0`; `p=0` returns `null`/`None` because no finite fair odds exist;
- multiclass Brier score is `sum((p_i - y_i)^2)` across the validated field;
- categorical log loss uses the natural logarithm `-ln(p_winner)`.

The validator never repairs, renormalizes or silently drops invalid entries. It raises an explicit validation error so callers can abstain and preserve the diagnostic. The implementation is in `services/api/app/probability.py` and is covered by property-style edge-case tests in `services/api/tests/test_probability.py`.

