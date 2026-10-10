# Evidence-grounded claim validation

RIL-047 defines the claim boundary for any future research-assistant output. A factual claim must carry one or more immutable source IDs, model IDs, a timezone-aware observation timestamp, an explicit data mode and at least one limitation. The metadata is evidence context; it does not by itself establish licensing, official status, currentness or model validation.

Probability claims additionally require a finite value in the inclusive range 0–1 and an explicit supporting-evidence flag. Currentness claims require a recorded freshness verification. Source assertions require rights or provenance verification. Missing evidence raises a validation error rather than producing an estimate or a stronger wording.

The checked-in fixture is synthetic and offline. It contains accepted factual/illustrative probability examples and negative cases for unsupported probability, currentness and source assertions. It does not enable scraping, create a live-source claim, or change the project’s `BLOCKED_EXTERNAL_DEPENDENCY` checkpoint.
