# Stable watchlists and blackbook tracking

RIL-043 keeps a stable watch ID and canonical entity ID while source IDs, names, and providers change. Identity/source changes append events and update the current projection; the original event remains available for audit.

Watch targets support `ACTIVE`, `PAUSED`, and `REMOVED` states. Pause, resume, and removal are lifecycle events, not destructive deletes. Removed targets remain historical and cannot be silently reactivated or changed. All event timestamps are timezone-aware.

The fixture demonstrates a runner surviving a provider migration and name change, then being paused. It is synthetic identity evidence only and does not create external alerts, wagering, or execution paths.
