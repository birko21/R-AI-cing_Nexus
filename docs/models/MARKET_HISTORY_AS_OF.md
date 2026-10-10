# Timestamped market snapshots and as-of history

RIL-037 reconstructs quote history using only records whose source timestamp and retrieval timestamp are both at or before the requested forecast cutoff. A later quote, including a closing quote, cannot leak into an earlier decision.

The reconstruction classifies the latest eligible quote as `AVAILABLE`, `DELAYED`, `STALE`, or `CLOSING`. It returns `MISSING` when no eligible quote exists. `CLOSING` is an explicit quote phase, not a fallback for missing or earlier prices. Delayed quotes are identified when retrieval lags the source timestamp beyond policy; stale quotes exceed the configured source-age threshold.

History is append-only. The as-of method requires a timezone-aware cutoff and ignores future source timestamps. The checked-in fixture demonstrates live-before-close, closing-after-close, and missing-mapping replay using synthetic data only.
