# Forecast explainability contract

`services/api/app/explainability.py` builds deterministic explanations from verified forecast outputs. Each explanation includes predicted probability, fair decimal odds, model/version/timestamp, material feature contributions, source evidence references, missing or unreliable inputs, uncertainty intervals, calibration status and form-versus-market probability differences.

The module does not generate probabilities and has no LLM dependency. It rejects post-race starting-price features and invalid probability or uncertainty inputs. Any future language-model explanation layer must receive this structured output and may only paraphrase verified fields and limitations.
