# Model assurance workflow

`services/api/app/assurance.py` creates a hashed assurance packet for a model
artifact and evaluation. It requires separate leakage-audit, split-review and
calibration-review statuses, then keeps the packet `HOLD` until an independent
review reference and an owner decision reference with explicit approval are
recorded.

The packet has `promotion_authority: NONE`. Even a passing packet is evidence
for a manual registry decision; it cannot promote a model, enable a provider,
or turn synthetic metrics into a validated real-world claim.
