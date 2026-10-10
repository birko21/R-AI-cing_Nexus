# Source health, reissues, coverage and kill-switch operations

RIL-035 evaluates provider observations without changing historical receipts. The monitor detects schema drift, late revisions, outages, stale data, coverage gaps, and quota exhaustion.

Schema drift, outages, and exhausted quotas are critical signals and produce a `DISABLED` snapshot. Late revisions, stale data, and coverage gaps produce a `DEGRADED` snapshot unless another critical signal is present. The health snapshot records the signal kind, severity, detail, check time, and whether capabilities were disabled.

Applying a kill switch returns a new capability policy with `enabled=false` and a reason. It does not mutate the previous policy, raw envelopes, replay fixtures, or historical forecasts. A warning-only snapshot leaves capabilities enabled while exposing the degradation for operations review.

The SQL migration stores append-only health events. The checked-in dashboard fixture injects a schema-drift failure against synthetic data only; it is not evidence of a live source, availability, or provider approval.
