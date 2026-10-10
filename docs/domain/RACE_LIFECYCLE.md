# Race lifecycle and revision events

The lifecycle is an append-only event stream. A correction or field change appends a new event and field revision; no prior event, forecast or selection is edited.

## State transitions

```text
SCHEDULED -> ACCEPTANCES -> FINAL_FIELDS -> OFFICIAL
     |             |              |
     v             v              v
 POSTPONED     POSTPONED       ABANDONED
     |             |
     +--> SCHEDULED
```

`SCRATCHING`, `RESERVE` and `CORRECTION` are field events that retain the current race status while appending a new field revision. `OFFICIAL` and `ABANDONED` are terminal statuses for state transitions; later corrections are addenda, not mutations.

Every event carries a race ID, code, event type, status, field revision, observed/effective timestamps and an immutable payload. The database trigger rejects updates and deletes.
