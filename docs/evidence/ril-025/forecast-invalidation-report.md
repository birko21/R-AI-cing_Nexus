# RIL-025 forecast invalidation report

RIL-025 keeps archived forecast records immutable while tracking field changes in a separate append-only invalidation ledger.

- A scratching, reserve activation or correction creates a new field revision and invalidates the prior forecast.
- The prior forecast remains retrievable by its original forecast ID and field revision.
- A new valid revision may be archived under a new forecast ID; the prior record is never overwritten.
- Coupled-entry and dead-heat cases abstain rather than receive fabricated probabilities; dead heats are excluded from primary scoring.
- Repeating the same invalidation event is idempotent; changing an existing invalidation raises an immutable-archive error.
- An `ABSTAIN` candidate cannot be stored as an active forecast record.

Focused command: `.venv\Scripts\python.exe -m pytest services/api/tests/test_forecast_invalidation.py -q`

