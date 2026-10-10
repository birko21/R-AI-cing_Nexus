# Historical feature contracts

RIL-061 adds `historical-features-v1` in `services/api/app/historical_features.py`.

Every observation records provider, dataset reference, racing code, race and participant identities, units, transformation, observation time, optional publication time, retrieval time, explicit pre-race eligibility time, receipt ID, rights state, retention class, quality state and identity evidence. Generated records also retain the feature-generation version and missingness reason.

The generator fails closed or excludes explicitly when:

- a source observation is after the forecast cutoff, has a future retrieval/publication time or lacks an eligible timing proof;
- rights are unapproved or retention is unknown;
- units do not match the declared feature definition;
- source quality is invalid, conflicting or duplicated;
- a runner is not in the exact field;
- records from multiple providers share a participant without exact/reconciled identity evidence.

Missing critical features remain missing. The generator never silently imputes values. Race z-scores are calculated only from eligible runners in the same race and feature family. Starting price is not part of the default pre-race definitions.
