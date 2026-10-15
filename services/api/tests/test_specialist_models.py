from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

import pytest

from app.specialist_models import (
    FeatureObservation,
    MODEL_STATUS,
    materialize_specialist_inputs,
    model_feature_set,
    specialist_model_manifest,
)


CUTOFF = datetime(2026, 1, 15, 1, 0, tzinfo=timezone.utc)
ROOT = Path(__file__).resolve().parents[3]


def observation(participant: str, feature: str, value: float, receipt: str, *, when: datetime = CUTOFF - timedelta(minutes=10), rights: str = "SYNTHETIC") -> FeatureObservation:
    return FeatureObservation(participant, feature, value, when, when + timedelta(minutes=1), receipt, rights)


def test_each_code_has_independent_form_market_and_combined_manifests() -> None:
    for code in ("THOROUGHBRED", "HARNESS", "GREYHOUND"):
        form = model_feature_set(code, "FORM_ONLY")
        market = model_feature_set(code, "MARKET_ONLY")
        combined = model_feature_set(code, "COMBINED")
        assert form
        assert market
        assert combined == form | market
        assert specialist_model_manifest(code, "COMBINED")["model_status"] == MODEL_STATUS

    assert "jockey_effect" in model_feature_set("THOROUGHBRED", "FORM_ONLY")
    assert "driver_effect" in model_feature_set("HARNESS", "FORM_ONLY")
    assert "box" in model_feature_set("GREYHOUND", "FORM_ONLY")


def test_committed_specialist_manifest_covers_all_code_and_family_lanes() -> None:
    manifest = json.loads((ROOT / "fixtures" / "synthetic" / "specialist_models_v1.json").read_text(encoding="utf-8"))

    assert manifest["schema_version"] == "specialist-model-manifests-v1"
    assert manifest["data_mode"] == "SYNTHETIC_ONLY"
    assert manifest["model_status"] == "ILLUSTRATIVE_NOT_VALIDATED"
    assert len(manifest["models"]) == 9
    assert {(item["code"], item["family"]) for item in manifest["models"]} == {
        (code, family) for code in ("GREYHOUND", "HARNESS", "THOROUGHBRED")
        for family in ("COMBINED", "FORM_ONLY", "MARKET_ONLY")
    }
    assert all("independent_assurance" in item["validation_required"] for item in manifest["models"])
    body = {key: value for key, value in manifest.items() if key != "manifest_hash"}
    expected_hash = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()
    assert manifest["manifest_hash"] == expected_hash


def test_inputs_are_race_normalised_and_future_or_unapproved_observations_are_excluded() -> None:
    observations = (
        observation("runner-a", "raw_speed", 10.0, "r-a"),
        observation("runner-b", "raw_speed", 20.0, "r-b"),
        observation("runner-a", "available_back_volume", 100.0, "m-a"),
        observation("runner-b", "available_back_volume", 50.0, "m-b"),
        observation("runner-a", "raw_speed", 99.0, "future", when=CUTOFF),
        observation("runner-a", "raw_speed", 88.0, "restricted", rights="UNASSESSED"),
    )
    snapshot = materialize_specialist_inputs(
        code="THOROUGHBRED", family="COMBINED", race_id="race-1", cutoff=CUTOFF,
        participant_ids=("runner-a", "runner-b"), observations=observations,
    )

    assert snapshot.model_status == "ILLUSTRATIVE_NOT_VALIDATED"
    assert snapshot.values["runner-a"]["raw_speed"] == -1.0
    assert snapshot.values["runner-b"]["raw_speed"] == 1.0
    assert snapshot.excluded_future_receipt_ids == ("future",)
    assert snapshot.excluded_unapproved_receipt_ids == ("restricted",)
    assert "starting_price_diagnostic" not in snapshot.values["runner-a"]


def test_specialist_input_rejects_duplicate_field_membership_and_duplicate_observations() -> None:
    with pytest.raises(ValueError, match="duplicate participant"):
        materialize_specialist_inputs(
            code="GREYHOUND", family="FORM_ONLY", race_id="race-1", cutoff=CUTOFF,
            participant_ids=("runner-a", "runner-a"), observations=(),
        )
    with pytest.raises(ValueError, match="duplicate specialist"):
        materialize_specialist_inputs(
            code="HARNESS", family="FORM_ONLY", race_id="race-1", cutoff=CUTOFF,
            participant_ids=("runner-a",), observations=(
                observation("runner-a", "raw_speed", 10.0, "one"),
                observation("runner-a", "raw_speed", 11.0, "two"),
            ),
        )
