# Operations, quotas, costs and provider kill switches

RIL-058 records job count, source/provider, latency, success/error status, input/output tokens and estimated AUD spend in an append-only local ledger. Spend and token ratios produce explicit `WARN_50`, `WARN_80` and `CAP_100` levels. At cap, noncritical outbound work is disabled; critical control work remains allowed unless its provider is explicitly kill-switched.

The checked-in dashboard fixture is synthetic and offline. It does not enable a provider, create credentials, or claim real cloud costs. Production telemetry and billing integrations remain deployment-specific follow-up work.
