from __future__ import annotations

import pytest

from app.forecast_archive import ForecastArchive, ImmutableArchiveError, create_forecast_manifest


def manifest(forecast_id: str, field_revision: str):
    return create_forecast_manifest(
        forecast_id=forecast_id, race_id="race-1", field_revision=field_revision,
        cutoff="2026-01-15T03:30:00Z", feature_snapshot={"active": ["entry-1", "entry-2"]},
        model_descriptor={"model_id": "B0_UNIFORM", "model_version": "b0-uniform-v1"},
        active_runner_ids=["entry-1", "entry-2"], data_mode="SYNTHETIC_ONLY",
        diagnostic_flags=["FIELD_VALID"], output={"probabilities": {"entry-1": 0.5, "entry-2": 0.5}},
    )


def test_new_field_revision_invalidates_old_forecast_without_mutating_it() -> None:
    archive = ForecastArchive()
    old = manifest("forecast-r1", "field-r1")
    new = manifest("forecast-r2", "field-r2")
    archive.append_ready(old, forecast_status="READY")

    event = archive.invalidate(
        old.forecast_id, new_field_revision="field-r2", reason="SCRATCHING_OBSERVED", invalidated_at="2026-01-15T04:00:00Z"
    )
    archive.append_ready(new, forecast_status="READY")

    assert event.prior_field_revision == "field-r1"
    assert archive.get(old.forecast_id)["field_revision"] == "field-r1"
    assert archive.get_invalidation(old.forecast_id)["new_field_revision"] == "field-r2"
    assert not archive.is_current(old.forecast_id, "field-r2")
    assert archive.is_current(new.forecast_id, "field-r2")


def test_invalidation_is_append_only_and_idempotent() -> None:
    archive = ForecastArchive()
    old = manifest("forecast-r1", "field-r1")
    archive.append_ready(old, forecast_status="READY")
    kwargs = {"new_field_revision": "field-r2", "reason": "CORRECTION", "invalidated_at": "2026-01-15T04:00:00Z", "event_type": "CORRECTION"}

    first = archive.invalidate(old.forecast_id, **kwargs)
    second = archive.invalidate(old.forecast_id, **kwargs)

    assert first.to_dict() == second.to_dict()
    with pytest.raises(ImmutableArchiveError, match="invalidation is immutable"):
        archive.invalidate(old.forecast_id, new_field_revision="field-r3", reason="OTHER", invalidated_at="2026-01-15T05:00:00Z")


def test_abstained_forecast_cannot_become_active_archive_record() -> None:
    archive = ForecastArchive()

    with pytest.raises(ImmutableArchiveError, match="abstained"):
        archive.append_ready(manifest("forecast-abstain", "field-r1"), forecast_status="ABSTAIN")


def test_invalidation_requires_a_new_revision() -> None:
    archive = ForecastArchive()
    old = manifest("forecast-r1", "field-r1")
    archive.append_ready(old, forecast_status="READY")

    with pytest.raises(ImmutableArchiveError, match="new field revision"):
        archive.invalidate(old.forecast_id, new_field_revision="field-r1", reason="SCRATCHING", invalidated_at="2026-01-15T04:00:00Z")

