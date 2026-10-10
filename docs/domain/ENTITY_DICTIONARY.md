# Canonical entity dictionary

The domain model uses namespaced source identities. A display name is never an identity key and cannot be used to join records.

## Identity pattern

Every source-backed entity has:

`<RACING_CODE>:<SOURCE_SYSTEM>:<SOURCE_ID>`

For example, `THOROUGHBRED:synthetic:meeting-001` and `HARNESS:synthetic:meeting-001` are intentionally different identifiers even when the source ID or display name is the same.

## Entities

| Entity | Canonical key | Required relationships | Notes |
|---|---|---|---|
| Code | `THOROUGHBRED`, `HARNESS`, `GREYHOUND` | none | Closed vocabulary for the MVP. |
| Meeting | `meeting_id` | code | Australian scheduled meeting; source and observed timestamps are persisted. |
| Race | `race_id` + `field_revision` | meeting, code | A corrected field is a new revision, never an overwrite. |
| Participant/runner | `participant_id` | code | Code is part of identity; names are display attributes only. |
| Entry | `entry_id` | race, participant, code | An exact entry in an exact field revision. |
| Market-selection mapping | `mapping_id` | race, field revision, exact entry | Mapping requires provider market/selection IDs; name-only mapping is rejected. |

The domain registry and tests enforce cross-code relationship checks and canonical-ID collision checks. Persistent storage is synthetic-only until rights and provider controls are separately approved.
