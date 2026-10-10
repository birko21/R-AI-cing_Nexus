# Thoroughbred specialist features

RIL-051 defines a synthetic, provenance-preserving descriptive feature snapshot for class, distance, track/going, barrier, weight, pace and sectional inputs. Each feature is either a numeric value or `null` with a missingness reason and source receipt IDs. Only facts observed before the UTC cutoff are included; future receipts are listed separately.

The snapshot is labelled `DESCRIPTIVE_ASSOCIATION_ONLY`. It must not be interpreted as causal attribution, a validated predictor, a current live fact or a wagering recommendation. The checked-in fixture is synthetic and remains separate from the blocked real-source approval work.
