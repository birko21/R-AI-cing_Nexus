# Four-provider modelling feature catalogue

This catalogue defines what should be investigated, not what is currently available or validated. A feature is eligible only when the source provides a trustworthy pre-race timestamp, exact runner identity, permitted retention/model use and sufficient historical coverage.

## Independent code specialists

| Feature family | Thoroughbred | Harness | Greyhound | Temporal and quality rule |
|---|---|---|---|---|
| Historical performance, recent form, trends | runs, finish positions, margins, class-adjusted form, recency and trend slopes | starts, placings, margins, gait/break indicators, recent activity | starts, placings, margins, trouble/interference history and recency | Aggregate only prior runs; preserve missingness and source receipts. |
| Distance and venue suitability | distance/track/going match, venue profile, rail and surface | distance/start-type/track suitability, venue and turn profile | distance/track/box suitability, bend and surface profile | Use only facts known before cutoff; no post-race track classification. |
| Raw and adjusted speed | raw time, speed figure, variant-adjusted figure, class-normalised figure | mile rate, raw/adjusted speed and gait-adjusted rate | raw time, first-split speed, early acceleration and track-variant adjustment | Adjustment reference set must be historical-only and versioned. |
| Sectionals and finishing speed | first/last sectional, late split, finish-speed index | sectionals, last-mile/last-half and late fade | first split, bend-to-line, finish-speed index | Reject unverified or post-publication sectional timestamps. |
| Class and field strength | grade/class, prize band, opposition rating, field depth | grade, class, stake band and opponent strength | grade, class and field strength | Recompute strength without using the target race result. |
| Draw and position | barrier, map, early speed and likely position | row/barrier, start type, gate speed and running line | box, first bend position and crowding risk | Draw is pre-race; expected position is a model feature, not a realised result. |
| Participants | jockey/trainer effects, changes and stable/partnership context | driver/trainer effects, stable form and driver change | trainer/kennel effects and recent handler activity | Shrink estimates; avoid sparse identifiers and future knowledge. |
| Fitness and activity | days since run, preparation pattern, trials and workload | days since start, trial/workload pattern and break risk | days since run, recent activity and recovery pattern | Activity records need publication/receipt proof. |
| Pace and interactions | expected pace, speed map, runner interactions and contested lead | early pressure, leader/back-marker interactions and gait scenarios | early pace, crowding, interference and pairwise draw interactions | Interaction features must be computed from the pre-race field only. |
| Market intelligence | provider prices, Betfair back/lay, movement, available size and matched liquidity | same, subject to code coverage and licensing | same, subject to code coverage and licensing | Market snapshots require exact market/selection mapping and as-of reconstruction. |

## Provider-derived fields

| Provider | Safe investigation candidates | Known gaps from the audit |
|---|---|---|
| FormFav | Thoroughbred card fields, barrier, weight, jockey, trainer, form, distance and scratch state | No durable upstream IDs, no source version, no market/history/result surface evidenced. |
| PuntersEdge | Settled fixed Win/Place prices, horse-form runs, starting price and returned form metadata | Personal-use evidence only; long retention and model-training rights not evidenced; live result validation is not a historical model dataset. |
| Krok Odds | Win/Place market enrichment, runner form, finishing order and any authorised tote/BSP fields | The live recheck did not establish complete dividends, free-tier access or long historical coverage. |
| Betfair Exchange | Catalogue identity, selection IDs, pre-race back/lay prices, price movement, available volume, matched volume and authorised SP | The sibling code does not yet normalize exchange ladders/liquidity histories; closed-market reconstruction and licence/retention/model rights are open gates. |

## Model families

For each racing code, develop and evaluate separate versions of:

- **Form-only:** historical performance, suitability, speed/sectionals, class, draw, participant effects, fitness, pace and interactions. No market inputs.
- **Market-only:** provider price-implied probabilities, movement, spread, available volume, matched liquidity and market-state indicators. No form inputs. Starting price is retained only as a separately authorised post-race diagnostic, never as a default pre-race feature.
- **Combined:** form-only plus market-only features with provider/source indicators and missingness controls.

All three families must be independently specified for thoroughbred, harness and greyhound racing. Shared engineering utilities are acceptable; shared coefficients, target definitions or code assumptions are not assumed valid.

## Evaluation contract

Every feature family and provider contribution is an ablation against a strong code-specific baseline using chronological walk-forward splits. The report must include race-level log loss, multiclass Brier score, calibration curves/reliability, coverage/abstention, rank/value diagnostics where authorised, confidence intervals or bootstrap uncertainty, and a leakage audit.

No feature may be credited when its timestamp is unknown, its source join is approximate, its runner is duplicated, its value is derived from the target result, or its licence does not permit model use. Missing data stays missing; it is not replaced with a favourable default.
