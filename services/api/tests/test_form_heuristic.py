from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from app.form_heuristic import FormRace, FormRun, FormRunner, build_b1_forecast


ROOT = Path(__file__).resolve().parents[3]
CUTOFF = datetime(2026, 1, 15, 3, 30, tzinfo=timezone.utc)
CHECKSUM = "fixture-checksum-v1"


def run(participant: str, day: int, finish: int, distance: int = 1200, hour: int = 0) -> FormRun:
    return FormRun(participant, datetime(2025, 12, day, hour, tzinfo=timezone.utc), distance, finish)


def runner(number: int, participant: str, *runs: FormRun, **kwargs: object) -> FormRunner:
    return FormRunner(f"entry-{number}", participant, number, runs=tuple(runs), **kwargs)


def race(*runners: FormRunner, code: str = "THOROUGHBRED", target_distance: int | None = 1200, field_status: str = "FINAL_FIELDS") -> FormRace:
    return FormRace("race-test", code, "field-r1", field_status, target_distance, tuple(runners))


def test_b1_uses_only_pre_cutoff_runs_and_normalizes_probabilities() -> None:
    future = FormRun("p1", datetime(2026, 1, 15, 12, tzinfo=timezone.utc), 1200, 1)
    forecast = build_b1_forecast(
        race(
            runner(1, "p1", run("p1", 11, 1), run("p1", 12, 3), future),
            runner(2, "p2", run("p2", 11, 2), run("p2", 12, 2)),
        ),
        cutoff=CUTOFF,
        manifest_checksum=CHECKSUM,
    )

    assert forecast.status == "READY"
    assert sum(item.probability or 0 for item in forecast.runners) == pytest.approx(1.0)
    assert all(item.features and item.features.support_count == 2 for item in forecast.runners)
    assert forecast.diagnostics == ("PRE_CUTOFF_RUNS_ONLY", "MINIMUM_SUPPORT=2", "NORMALIZED_PROBABILITIES")
    assert forecast.model_id == "B1_FORM_HEURISTIC"
    assert forecast.model_version == "b1-form-v1"
    assert forecast.model_status == "ILLUSTRATIVE_NOT_VALIDATED"


def test_b1_weights_are_code_specific_and_explicit() -> None:
    runs_one = (run("p1", 11, 1), run("p1", 12, 4))
    runs_two = (run("p2", 11, 2), run("p2", 12, 3))
    thoroughbred = build_b1_forecast(race(runner(1, "p1", *runs_one), runner(2, "p2", *runs_two), code="THOROUGHBRED"), cutoff=CUTOFF, manifest_checksum=CHECKSUM)
    greyhound = build_b1_forecast(race(runner(1, "p1", *runs_one), runner(2, "p2", *runs_two), code="GREYHOUND"), cutoff=CUTOFF, manifest_checksum=CHECKSUM)

    assert thoroughbred.weights != greyhound.weights
    assert thoroughbred.smoothing == 0.1
    assert thoroughbred.minimum_support == 2
    assert thoroughbred.runners[0].features != greyhound.runners[0].features


def test_b1_abstains_on_missing_support_and_unsupported_inputs() -> None:
    insufficient = build_b1_forecast(
        race(runner(1, "p1", run("p1", 11, 1)), runner(2, "p2", run("p2", 11, 2))),
        cutoff=CUTOFF,
        manifest_checksum=CHECKSUM,
    )
    coupled = build_b1_forecast(
        race(runner(1, "p1", run("p1", 11, 1), run("p1", 12, 2), coupled_group="a"), runner(2, "p2", run("p2", 11, 2), run("p2", 12, 3))),
        cutoff=CUTOFF,
        manifest_checksum=CHECKSUM,
    )
    unsupported = build_b1_forecast(
        race(runner(1, "p1", run("p1", 11, 1), run("p1", 12, 2)), runner(2, "p2", run("p2", 11, 2), run("p2", 12, 3)), code="UNKNOWN"),
        cutoff=CUTOFF,
        manifest_checksum=CHECKSUM,
    )

    assert insufficient.abstention_reason == "INSUFFICIENT_SUPPORT"
    assert coupled.abstention_reason == "COUPLED_ENTRY"
    assert unsupported.abstention_reason == "UNSUPPORTED_CODE"
    assert insufficient.runners == tuple()


def test_b1_abstains_for_invalid_field_or_missing_distance() -> None:
    invalid_field = build_b1_forecast(
        race(runner(1, "p1", run("p1", 11, 1), run("p1", 12, 2)), runner(2, "p2", run("p2", 11, 2), run("p2", 12, 3)), field_status="PROVISIONAL"),
        cutoff=CUTOFF,
        manifest_checksum=CHECKSUM,
    )
    missing_distance = build_b1_forecast(
        race(runner(1, "p1", run("p1", 11, 1), run("p1", 12, 2)), runner(2, "p2", run("p2", 11, 2), run("p2", 12, 3)), target_distance=None),
        cutoff=CUTOFF,
        manifest_checksum=CHECKSUM,
    )

    assert invalid_field.abstention_reason == "FIELD_NOT_VALID"
    assert missing_distance.abstention_reason == "MISSING_TARGET_DISTANCE"


def test_committed_b1_manifest_records_inputs_weights_and_mode() -> None:
    manifest = json.loads((ROOT / "fixtures" / "synthetic" / "forecasts_b1.json").read_text(encoding="utf-8"))

    assert manifest["schema_version"] == "ril-022-b1-v1"
    assert manifest["model"]["inputs"] == ["pre_cutoff_historical_runs", "target_distance", "field_membership"]
    assert manifest["model"]["minimum_support"] == 2
    assert manifest["model"]["smoothing"] == 0.1
    assert len(manifest["forecasts"]) == 6
    assert all(item["status"] == "READY" for item in manifest["forecasts"])
    assert all(item["model_status"] == "ILLUSTRATIVE_NOT_VALIDATED" for item in manifest["forecasts"])
    assert all(item["data_mode"] == "SYNTHETIC_ONLY" for item in manifest["forecasts"])

