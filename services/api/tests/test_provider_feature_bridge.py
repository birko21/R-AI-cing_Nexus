from datetime import datetime, timezone

from app.historical_features import FeatureDefinition, generate_feature_snapshot
from app.provenance import RawEnvelope, payload_sha256
from app.provider_feature_bridge import bridge_provider_feature_observations


UTC = timezone.utc
CUTOFF = datetime(2026, 1, 15, 1, tzinfo=UTC)


def envelope(rows: list[dict[str, object]], *, rights: str = "SYNTHETIC", retrieved_at: datetime = datetime(2026, 1, 15, 0, 30, tzinfo=UTC)) -> RawEnvelope:
    payload = {"feature_observations": rows}
    return RawEnvelope(
        envelope_id="receipt-1", source_identifier="synthetic://provider/features", payload=payload,
        payload_sha256=payload_sha256(payload), schema_version="features-v1", retrieved_at=retrieved_at,
        first_observed_at=retrieved_at, data_mode="SYNTHETIC_ONLY" if rights == "SYNTHETIC" else "SCRAPED_PUBLIC", rights_state=rights,
    )


def row(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "participant_id": "runner-1", "provider_participant_id": "provider-1", "feature_name": "raw_speed",
        "value": 12.0, "unit": "m/s", "observed_at": "2026-01-15T00:00:00Z",
        "pre_race_eligible_at": "2026-01-15T00:00:00Z", "retention_class": "SYNTHETIC_FIXTURE",
    }
    values.update(overrides)
    return values


def test_bridge_emits_only_eligible_rows_and_materializes_snapshot() -> None:
    result = bridge_provider_feature_observations(
        envelope([row()]), provider_id="synthetic", dataset_reference="provider-features-v1",
        code="THOROUGHBRED", race_id="race-1", cutoff=CUTOFF,
    )

    assert len(result.observations) == 1
    snapshot = generate_feature_snapshot(
        race_id="race-1", code="THOROUGHBRED", cutoff=CUTOFF, participant_ids=("runner-1",),
        definitions={"raw_speed": FeatureDefinition("raw_speed", "m/s")}, observations=result.observations,
    )
    assert snapshot.records["runner-1"]["raw_speed"].value == 0.0


def test_bridge_quarantines_unknown_timestamps_rights_and_post_cutoff_rows() -> None:
    result = bridge_provider_feature_observations(
        envelope([
            row(observed_at=None),
            row(feature_name="restricted", observed_at="2026-01-15T00:00:00Z"),
            row(feature_name="future", observed_at="2026-01-15T02:00:00Z"),
        ], rights="UNASSESSED"),
        provider_id="synthetic", dataset_reference="provider-features-v1", code="THOROUGHBRED",
        race_id="race-1", cutoff=CUTOFF,
    )

    assert result.observations == ()
    assert {item.reason for item in result.quarantines} == {"UNKNOWN_TIMESTAMP", "RIGHTS_NOT_APPROVED"}

    future = bridge_provider_feature_observations(
        envelope([row(feature_name="future", observed_at="2026-01-15T02:00:00Z")]),
        provider_id="synthetic", dataset_reference="provider-features-v1", code="THOROUGHBRED",
        race_id="race-1", cutoff=CUTOFF,
    )
    assert future.observations == ()
    assert future.quarantines[0].reason == "POST_CUTOFF"

    impossible = bridge_provider_feature_observations(
        envelope([row(feature_name="impossible", observed_at="2026-01-15T00:45:00Z")]),
        provider_id="synthetic", dataset_reference="provider-features-v1", code="THOROUGHBRED",
        race_id="race-1", cutoff=CUTOFF,
    )
    assert impossible.observations == ()
    assert impossible.quarantines[0].reason == "INVALID_PROVIDER_FEATURE"


def test_bridge_quarantines_missing_retention_and_unavailable_receipt_times() -> None:
    missing_retention = bridge_provider_feature_observations(
        envelope([row(retention_class="")]), provider_id="synthetic", dataset_reference="provider-features-v1",
        code="THOROUGHBRED", race_id="race-1", cutoff=CUTOFF,
    )
    assert missing_retention.observations == ()
    assert missing_retention.quarantines[0].reason == "RETENTION_UNSPECIFIED"

    retrieved_after_cutoff = bridge_provider_feature_observations(
        envelope([row()], retrieved_at=CUTOFF + datetime.resolution), provider_id="synthetic",
        dataset_reference="provider-features-v1", code="THOROUGHBRED", race_id="race-1", cutoff=CUTOFF,
    )
    assert retrieved_after_cutoff.observations == ()
    assert retrieved_after_cutoff.quarantines[0].reason == "POST_CUTOFF"

    published_after_cutoff = bridge_provider_feature_observations(
        envelope([row(published_at="2026-01-15T01:00:01Z")]), provider_id="synthetic",
        dataset_reference="provider-features-v1", code="THOROUGHBRED", race_id="race-1", cutoff=CUTOFF,
    )
    assert published_after_cutoff.observations == ()
    assert published_after_cutoff.quarantines[0].reason == "POST_CUTOFF"


def test_bridge_quarantines_eligibility_after_retrieval() -> None:
    result = bridge_provider_feature_observations(
        envelope([row(pre_race_eligible_at="2026-01-15T00:45:00Z")]), provider_id="synthetic",
        dataset_reference="provider-features-v1", code="THOROUGHBRED", race_id="race-1", cutoff=CUTOFF,
    )

    assert result.observations == ()
    assert result.quarantines[0].reason == "INVALID_PROVIDER_FEATURE"
