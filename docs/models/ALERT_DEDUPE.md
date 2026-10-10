# Source-linked change events and alert deduplication

RIL-044 routes only confirmed, material change events into alerts. Each event carries its source system, immutable source receipt reference, observation timestamp, validity, suppression key, cause, and expiry. Unconfirmed or immaterial events are retained as events but do not alert.

Active alerts are deduplicated by suppression key. Replayed events return the existing active alert; after expiry, a later confirmed event may create a new alert. Expired alerts are not returned as active. Events and alerts are append-only, so replay and audit do not mutate prior records.

The fixture is synthetic and offline. It demonstrates confirmation gating, replay dedupe, and post-expiry re-alerting; it does not send external notifications or create wagering/execution behavior.
