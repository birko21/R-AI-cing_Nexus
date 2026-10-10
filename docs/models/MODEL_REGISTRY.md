# Model registry and assurance policy

RIL-030 stores model artifacts, evaluations, independent-assurance events and registry decisions as append-only records. Model artifacts retain their hash, feature schema, data mode and model status. Evaluations retain their split-manifest hash, metrics, sample count and mode. Rejected artifacts remain visible for audit.

Registry statuses are `INSUFFICIENT EVIDENCE`, `SHADOW`, `HOLD`, `BLOCK` and `CHAMPION`. `CHAMPION` is only accepted with a passing independent-assurance event and explicit manual owner approval. Automated promotion is rejected. A registry `CHAMPION` state is an internal, evidence-gated comparison status; it never changes `ILLUSTRATIVE_NOT_VALIDATED` into a real-world validation claim.

The append-only PostgreSQL migration is `migrations/versions/007_model_registry.py`. The deterministic registry fixture is `fixtures/synthetic/model_registry_v1.json`; verify it with:

```powershell
.venv\Scripts\python.exe scripts/generate_registry_fixture.py
```

