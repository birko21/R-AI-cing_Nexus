# Implied probability, overround and comparability

RIL-038 converts declared decimal, fractional, and American prices into implied probabilities. For a comparable market, the sum of implied probabilities is the overround and normalized probabilities divide each implied probability by that sum.

Comparison returns `NOT_COMPARABLE` rather than guessing when required quotes are missing, runners are scratched/reserves leaving fewer than two active selections, selections are duplicated, market identity or field revision differs, source timestamps exceed the configured skew window, or odds fail their declared price-type rules. This prevents incomplete or temporally mismatched books from becoming false comparisons.

The implementation is reference math only. It does not recommend a wager, infer profitability, place orders, access bookmaker credentials, or claim that synthetic or scraped prices are official. The fixture demonstrates a normalized book and conservative non-comparable outcomes.
