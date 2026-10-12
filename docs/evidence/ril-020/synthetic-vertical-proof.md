# Synthetic vertical proof

The local engineering path is now proven before view review. The executable
proof in `scripts/prove_synthetic_vertical.py` runs the provider-shaped
synthetic fixture through:

1. three-code ingestion with the local worker contract;
2. a second replay against the same append-only store, demonstrating
   idempotent skips;
3. a pre-race B0 baseline forecast using the persisted envelope checksum;
4. immutable forecast-manifest creation, verification, and replay; and
5. the fail-closed release gate.

The proof is deliberately limited to `SYNTHETIC_ONLY`. It asserts that no
quarantine occurs for the valid fixture, the replay does not duplicate stored
envelopes, the forecast is `READY`, the archived output reproduces exactly,
and the release status remains `LOCAL_SYNTHETIC_ONLY_HOLD` with activation and
promotion authority set to `NONE`.

Run locally from the repository root:

```text
.venv\\Scripts\\python.exe scripts/prove_synthetic_vertical.py
```

This is an engineering/data-plane proof, not evidence of real-world model
accuracy, licensed provider access, production readiness, or owner approval.

The associated verification run also passed 307 API tests, frontend typecheck,
frontend unit tests with `VITE_AUTH_REQUIRED=true`, the production frontend
build, all seven Playwright/axe browser tests, the security audit, contract
validation, and Render Blueprint validation.

The pressure harness repeats the ingestion/replay path across 25 cycles, checks
25 deterministic replay-manifest regenerations, and executes 25 tamper cases.
It is included in CI alongside the single-run proof.
