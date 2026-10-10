# Immutable personal selections and deliberate PASS records

RIL-041 adds a local owner journal for research decisions. Each record captures the authenticated user, race, field revision, decision time, optional exact entry, selection type, rationale, and optional forecast/quote references. `PASS` is a deliberate first-class record and may omit an entry; `WIN` and `PLACE` require one.

Selections and correction addenda are append-only. A correction never edits the original rationale, field revision, or references; it adds a separately identified addendum linked to the original selection and authenticated user. Cross-user addenda are rejected.

The API stores only local journal records and synthetic data mode in the current MVP. It does not create wagering, order, staking, bookmaker, or external execution paths.
