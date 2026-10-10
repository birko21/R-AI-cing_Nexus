"""Generate deterministic RIL-061 research and readiness evidence."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.historical_evaluation import ForecastCase, evaluate_forecasts  # noqa: E402
from app.model_benchmarks import (  # noqa: E402
    B1_WEIGHTS,
    BenchmarkRace,
    BenchmarkRunner,
    MarketInput,
    build_b0_forecast,
    build_b1_form_forecast,
    build_b2_market_forecast,
    build_b4_market_informed_ensemble,
)
from app.provider_readiness import build_provider_readiness_report  # noqa: E402


OUT = ROOT / "docs" / "evidence" / "ril-061"
UTC = timezone.utc


def synthetic_race(code: str, day: int) -> BenchmarkRace:
    cutoff = datetime(2026, 1, day, 1, tzinfo=UTC)
    weights = B1_WEIGHTS[code]
    strong = {feature: 2.0 for feature in weights}
    weak = {feature: 1.0 for feature in weights}
    return BenchmarkRace(
        race_id=f"ril061-{code.lower()}-{day}", code=code, cutoff=cutoff,
        runners=(BenchmarkRunner("a"), BenchmarkRunner("b")), form_features={"a": strong, "b": weak},
        market_inputs={
            "a": MarketInput(2.0, 2.2, cutoff - timedelta(minutes=2), 20.0, 18.0, 100.0),
            "b": MarketInput(4.0, 4.2, cutoff - timedelta(minutes=2), 20.0, 18.0, 100.0),
        },
    )


def main() -> None:
    forecasts: list[dict[str, object]] = []
    cases: list[ForecastCase] = []
    for code, day in (("THOROUGHBRED", 1), ("HARNESS", 2), ("GREYHOUND", 3)):
        race = synthetic_race(code, day)
        market = build_b2_market_forecast(race)
        for forecast in (build_b0_forecast(race), build_b1_form_forecast(race), market, build_b4_market_informed_ensemble(race)):
            forecasts.append(forecast.to_dict())
            if forecast.state == "READY":
                cases.append(ForecastCase(
                    race_id=race.race_id, code=code, observed_at=race.cutoff, model_id=forecast.model_id,
                    model_version=forecast.model_version, probabilities=forecast.probabilities, winner_entry_id="a",
                    outcome_status="SINGLE_WINNER", track="Synthetic", distance=1200, race_type="WIN",
                    feature_family=forecast.model_id, missingness=forecast.missingness,
                    market_probabilities=market.probabilities if market.state == "READY" else None,
                    fold_id=f"fold-{day:03d}", fold_role="TEST",
                ))
    evaluation = evaluate_forecasts(tuple(cases))
    payload = {
        "schema_version": "ril-061-evidence-v1",
        "status": "ILLUSTRATIVE_SYNTHETIC_ONLY",
        "validated_claim": False,
        "provider_readiness": build_provider_readiness_report(),
        "benchmarks": forecasts,
        "evaluation": evaluation,
        "b3_machine_learning": {"status": "NOT_AVAILABLE", "backend": "lightgbm_or_catboost", "reason": "Optional engine is not installed; no fallback is silently substituted."},
        "limitations": [
            "Synthetic fixture observations are not real racing history.",
            "No provider rights, retention or model-training approval is established.",
            "No predictive improvement, calibration or profitability claim is made.",
            "Post-race starting price is not used as a pre-race feature.",
        ],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "research-output.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "model-evaluation.json").write_text(json.dumps(evaluation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "provider-readiness.json").write_text(json.dumps(payload["provider_readiness"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"RIL-061 EVIDENCE VALID: forecasts={len(forecasts)} scored_cases={evaluation['scored_case_count']} output={OUT}")


if __name__ == "__main__":
    main()
