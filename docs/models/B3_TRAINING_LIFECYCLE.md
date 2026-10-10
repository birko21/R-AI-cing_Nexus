# B3 training lifecycle

`services/api/app/ml_models.py` implements a real optional LightGBM B3 backend and a separate CatBoost challenger backend.

The lifecycle is fail-closed:

- training rows require a code/family feature-schema hash, source receipts, rights state, cutoff and pre-race eligibility timestamp;
- each race must have exactly one winner and duplicate runner records are rejected;
- inference requires an exact feature schema, matching data mode and explicit pre-race eligibility proof for every runner;
- missing inputs, future eligibility timestamps and invalid artifacts produce `ABSTAIN` or `ModelArtifactError`;
- race scores are normalised to sum to one over the supplied field;
- model artifacts are inspectable JSON envelopes with backend-native model text, manifest hash, schema hash, dependency version, seed and SHA-256 identity;
- model status remains `ILLUSTRATIVE_NOT_VALIDATED` regardless of synthetic performance.

Pinned development/CI dependencies are in `services/api/requirements-ml.lock.txt`:

- LightGBM `4.7.0`
- CatBoost `1.2.10`

`scripts/generate_b3_synthetic_evidence.py` trains both backends independently for thoroughbred, harness and greyhound synthetic specialist inputs. Its output is evidence of reproducibility and contract operation only, not predictive validity.
