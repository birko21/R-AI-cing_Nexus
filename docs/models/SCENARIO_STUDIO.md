# Reproducible Scenario Studio

RIL-054 stores scenario assumptions, seed, bounded sample size, normalized inputs, observed fact IDs, hypotheses, model version, data mode and a deterministic output hash. Observed facts and hypotheses are separate fields so a scenario assumption cannot be mistaken for an observation.

The simulator is synthetic and deterministic for a given request. It bounds sample size and output values. When calibration is absent it returns `ABSTAIN` with `CALIBRATION_ABSENT` and no outputs; it never fills the gap with an estimate. The checked-in fixture is evidence of replay and abstention only, not a calibrated prediction or wagering capability.
