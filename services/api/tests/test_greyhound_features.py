from datetime import datetime, timezone

import pytest

from app.greyhound_features import GREYHOUND_FEATURES, GreyhoundFact, activate_reserve, materialize_greyhound_features


CUTOFF = datetime(2026, 1, 15, 3, 30, tzinfo=timezone.utc)


def test_greyhound_features_preserve_specialist_inputs_and_provenance() -> None:
    result = materialize_greyhound_features(
        race_id="race-1", participant_id="p1", cutoff=CUTOFF,
        facts=(GreyhoundFact("p1", datetime(2025, 12, 1, tzinfo=timezone.utc), "receipt-g-1", 4, 5.8, 0.7, "wide", "G5", "checked", "none"),),
    )
    assert set(result.features) == set(GREYHOUND_FEATURES)
    assert result.features["box"].value == 4
    assert result.features["first_split"].value == 5.8
    assert result.features["interference"].value == "none"
    assert result.included_receipt_ids == ("receipt-g-1",)


def test_reserve_activation_recomputes_only_authorised_features() -> None:
    original = materialize_greyhound_features(
        race_id="race-1", participant_id="p1", cutoff=CUTOFF,
        facts=(GreyhoundFact("p1", datetime(2025, 12, 1, tzinfo=timezone.utc), "old", 4, 5.8, 0.7, "wide", "G5", "none", "none"),),
    )
    updated = activate_reserve(
        original, GreyhoundFact("p1", datetime(2026, 1, 15, tzinfo=timezone.utc), "reserve", 1, 5.2, 0.9, "inside", "G4", "crowded", "checked"),
        authorised_features=frozenset({"box", "trouble"}),
    )
    assert updated.recomputed_features == ("box", "trouble")
    assert updated.features["box"].value == 1
    assert updated.features["trouble"].value == "crowded"
    assert updated.features["first_split"].value == original.features["first_split"].value
    assert updated.features["first_split"].source_receipt_ids == original.features["first_split"].source_receipt_ids


def test_missing_and_unsupported_states_fail_closed() -> None:
    result = materialize_greyhound_features(race_id="race-1", participant_id="p1", cutoff=CUTOFF, facts=())
    assert all(value.missing for value in result.features.values())
    with pytest.raises(ValueError, match="unsupported authorised"):
        activate_reserve(result, GreyhoundFact("p1", CUTOFF, "r"), authorised_features=frozenset({"unknown"}))
    with pytest.raises(ValueError, match="timezone-aware"):
        materialize_greyhound_features(race_id="race-1", participant_id="p1", cutoff=datetime(2026, 1, 15), facts=())
