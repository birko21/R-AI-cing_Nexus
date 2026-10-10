# Versioned feature materialization

RIL-026 materializes `features-v1` snapshots from common historical-run facts and code-specific feature schemas. Each snapshot records the race, participant, code, UTC cutoff, target distance, data mode, included source receipt IDs, excluded future receipt IDs, feature values, missingness reasons and a deterministic snapshot hash.

Common features are run count, mean finish position and best finish position. Thoroughbred adds distance-match rate and finish consistency. Harness and greyhound add distance-match rate and recent-finish rate. Missing values remain `null` with a reason; no fallback or fabricated value is inserted.

Only `observed_at < cutoff` facts contribute. A future-fact injection changes only the explicit excluded-future receipt list and never changes the materialized feature values. The fixed synthetic manifest is `fixtures/synthetic/features_v1.json`.

