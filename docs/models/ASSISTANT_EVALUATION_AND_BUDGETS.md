# Assistant evaluation and cost controls

RIL-050 maintains four offline safety cases: positive evidence, negative/missing data, contradiction/discrepancy, and prompt injection. The deterministic fixture responder is test evidence only; it is not a model and does not establish predictive or real-world validity.

The budget ledger enforces request count, input-token, output-token and spend ceilings before usage is recorded. A rejected reservation is a kill-switch event and leaves usage unchanged. The default assistant policy is `FEATURE_DISABLED` until the feature flag, rights approval and provider-policy approval are all true.

The checked-in report is synthetic and offline. No provider credential, external transmission, live scrape, wagering action or hidden execution path is enabled.
