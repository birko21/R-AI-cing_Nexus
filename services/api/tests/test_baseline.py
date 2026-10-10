from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from app.baseline import BaselineRace, BaselineRunner, build_b0_forecast


ROOT = Path(__file__).resolve().parents[3]
CUTOFF = datetime(2026, 1, 15, 3, 30, tzinfo=timezone.utc)
CHECKSUM = "fixture-checksum-v1"


def race(*runners: BaselineRunner, field_status: str = "FINAL_FIELDS", data_mode: str = "SYNTHETIC_ONLY") -> BaselineRace:
    return BaselineRace(
        race_id="THOROUGHBRED:synthetic:race-test",
        code="THOROUGHBRED",
        field_revision="THOROUGHBRED:synthetic:race-test:field-r1",
        field_status=field_status,
        runners=tuple(runners),
        data_mode=data_mode,
    )


@pytest.mark.parametrize("runner_count", [1, 2, 4])
def test_b0_assigns_one_over_n_to_active_eligible_runners(runner_count: int) -> None:
    forecast = build_b0_forecast(
        race(*(BaselineRunner(f"entry-{number}", number) for number in range(1, runner_count + 1))),
        cutoff=CUTOFF,
        manifest_checksum=CHECKSUM,
    )

    assert forecast.status == "READY"
    assert len(forecast.runners) == runner_count
    assert all(item.probability == pytest.approx(1 / runner_count) for item in forecast.runners)
    assert sum(item.probability or 0 for item in forecast.runners) == pytest.approx(1.0)
    assert forecast.model_id == "B0_UNIFORM"
    assert forecast.model_version == "b0-uniform-v1"
    assert forecast.model_status == "ILLUSTRATIVE_NOT_VALIDATED"
    assert forecast.data_mode == "SYNTHETIC_ONLY"


def test_b0_excludes_scratched_and_reserve_entries() -> None:
    forecast = build_b0_forecast(
        race(
            BaselineRunner("entry-1", 1),
            BaselineRunner("entry-2", 2, status="SCRATCHED", eligible=False),
            BaselineRunner("entry-3", 3),
            BaselineRunner("entry-4", 4, status="RESERVE", eligible=False),
        ),
        cutoff=CUTOFF,
        manifest_checksum=CHECKSUM,
    )

    assert [runner.entry_id for runner in forecast.runners] == ["entry-1", "entry-3"]
    assert [runner.probability for runner in forecast.runners] == [pytest.approx(0.5), pytest.approx(0.5)]


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"field_status": "PROVISIONAL"}, "FIELD_NOT_VALID"),
        ({"data_mode": "SCRAPED_PUBLIC"}, "UNSUPPORTED_DATA_MODE"),
    ],
)
def test_b0_abstains_when_field_or_mode_is_not_supported(kwargs: dict[str, str], reason: str) -> None:
    forecast = build_b0_forecast(
        race(BaselineRunner("entry-1", 1), BaselineRunner("entry-2", 2), **kwargs),
        cutoff=CUTOFF,
        manifest_checksum=CHECKSUM,
    )

    assert forecast.status == "ABSTAIN"
    assert forecast.runners == tuple()
    assert forecast.abstention_reason == reason


def test_b0_abstains_on_unsupported_outcome_coupling_and_incomplete_fields() -> None:
    coupled = build_b0_forecast(
        race(BaselineRunner("entry-1", 1, coupled_group="couple-a"), BaselineRunner("entry-2", 2)),
        cutoff=CUTOFF,
        manifest_checksum=CHECKSUM,
    )
    unsupported = build_b0_forecast(
        race(BaselineRunner("entry-1", 1), BaselineRunner("entry-2", 2)),
        cutoff=CUTOFF,
        manifest_checksum=CHECKSUM,
        unsupported_outcome="DEAD_HEAT",
    )
    incomplete = build_b0_forecast(race(), cutoff=CUTOFF, manifest_checksum=CHECKSUM)

    assert coupled.abstention_reason == "COUPLED_ENTRY"
    assert unsupported.abstention_reason == "UNSUPPORTED_OUTCOME"
    assert unsupported.diagnostics == ("DEAD_HEAT",)
    assert incomplete.abstention_reason == "INCOMPLETE_FIELD"


def test_b0_forecast_id_is_reproducible_and_cutoff_requires_timezone() -> None:
    subject = race(BaselineRunner("entry-1", 1), BaselineRunner("entry-2", 2))
    first = build_b0_forecast(subject, cutoff=CUTOFF, manifest_checksum=CHECKSUM)
    second = build_b0_forecast(subject, cutoff=CUTOFF, manifest_checksum=CHECKSUM)

    assert first.to_dict() == second.to_dict()
    with pytest.raises(ValueError, match="timezone-aware"):
        build_b0_forecast(subject, cutoff=datetime(2026, 1, 15, 3, 30), manifest_checksum=CHECKSUM)


def test_committed_b0_manifest_contains_ready_forecasts_and_edge_abstentions() -> None:
    manifest = json.loads((ROOT / "fixtures" / "synthetic" / "forecasts_b0.json").read_text(encoding="utf-8"))

    assert manifest["schema_version"] == "ril-021-b0-v1"
    assert manifest["model"] == {
        "data_mode": "SYNTHETIC_ONLY",
        "method": "1/n over active eligible runners",
        "model_id": "B0_UNIFORM",
        "model_status": "ILLUSTRATIVE_NOT_VALIDATED",
        "model_version": "b0-uniform-v1",
    }
    assert len(manifest["forecasts"]) == 6
    assert all(item["status"] == "READY" for item in manifest["forecasts"])
    assert all(item["data_mode"] == "SYNTHETIC_ONLY" for item in manifest["forecasts"])
    assert len(manifest["edge_case_abstentions"]) == 12
    assert {item["reason"] for item in manifest["edge_case_abstentions"]} >= {"COUPLED_ENTRY", "INCOMPLETE_FIELD", "NOT_AVAILABLE", "UNSUPPORTED_OUTCOME"}

