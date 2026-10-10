# Immutable forecast archive

RIL-024 creates a canonical manifest for each forecast. A manifest stores the forecast ID, race ID, exact field revision, UTC cutoff, feature snapshot and hash, model hash, active-runner hash, data mode, diagnostic flags and output. The manifest hash is derived from those immutable fields using canonical sorted JSON and SHA-256.

The local archive is append-only: repeating the exact same manifest is idempotent, while a changed payload under an existing forecast ID raises `ImmutableArchiveError`. Retrieval verifies the feature snapshot and manifest hashes. Replay compares canonical output JSON with the archived output and therefore detects changed probabilities without silently rewriting history.

The deterministic fixture archive is `fixtures/synthetic/forecast_archive.json`; verify it with:

```powershell
.venv\Scripts\python.exe scripts/generate_forecast_archive.py
```

