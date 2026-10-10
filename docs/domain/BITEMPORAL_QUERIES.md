# Bitemporal and `as_of` rules

Facts carry both event/effective time and system-valid/observation time:

- `source_event_at`: when the source says the event occurred.
- `published_at`: when the source made it available, nullable only when a verified receipt still proves availability.
- `observed_at`: when this application first observed the payload.
- `effective_from`/`effective_to`: the business validity interval.
- `system_valid_from`/`system_valid_to`: the application revision interval.

An `as_of` snapshot includes only facts with verified receipt proof that were observed and, when known, published by the cutoff. It chooses the latest valid revision for each fact key without replacing historical rows. A missing receipt proof or a future observation is excluded rather than guessed.
