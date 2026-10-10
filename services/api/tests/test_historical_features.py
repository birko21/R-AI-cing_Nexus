from datetime import datetime, timedelta, timezone

import pytest

from app.historical_features import FeatureDefinition, FeatureObservation, generate_feature_snapshot


UTC = timezone.utc
CUTOFF = datetime(2026, 1, 15, 1, tzinfo=UTC)


def obs(participant: str, feature: str, value: float | None, receipt: str, *, provider: str = "synthetic", dataset: str = "runs-v1", when: datetime = CUTOFF - timedelta(hours=1), rights: str = "SYNTHETIC", unit: str = "score", identity_link: str | None = None, evidence: str = "NAME_ONLY") -> FeatureObservation:
    return FeatureObservation(
        provider, dataset, "THOROUGHBRED", "race-1", participant, f"{provider}:{participant}", feature, value, unit,
        when, when, when + timedelta(minutes=1), when, receipt, rights, "SYNTHETIC_LOCAL",
        quality_state="VALID", identity_link_id=identity_link, identity_evidence=evidence,
    )


def definitions() -> dict[str, FeatureDefinition]:
    return {
        "historical_performance": FeatureDefinition("historical_performance", "score", critical=True),
        "raw_speed": FeatureDefinition("raw_speed", "m/s"),
        "pre_race_price": FeatureDefinition("pre_race_price", "decimal_odds", "NEGATE"),
    }


def test_feature_snapshot_is_versioned_provenance_rich_and_race_normalised() -> None:
    snapshot = generate_feature_snapshot(
        race_id="race-1", code="THOROUGHBRED", cutoff=CUTOFF, participant_ids=("p1", "p2"), definitions=definitions(),
        observations=(
            obs("p1", "historical_performance", 10.0, "r1"), obs("p2", "historical_performance", 20.0, "r2"),
            obs("p1", "raw_speed", 12.0, "s1", unit="m/s"), obs("p2", "raw_speed", 14.0, "s2", unit="m/s"),
        ),
    )
    assert snapshot.schema_version == "historical-features-v1"
    assert snapshot.records["p1"]["historical_performance"].value == pytest.approx(-1.0)
    record = snapshot.records["p1"]["raw_speed"]
    assert record.source_provider == "synthetic"
    assert record.dataset_reference == "runs-v1"
    assert record.pre_race_eligible_at is not None
    assert record.generation_version == "historical-features-v1"
    assert snapshot.critical_missing == ()


def test_future_postrace_rights_and_identity_conflicts_are_excluded_without_imputation() -> None:
    snapshot = generate_feature_snapshot(
        race_id="race-1", code="THOROUGHBRED", cutoff=CUTOFF, participant_ids=("p1", "p2"), definitions=definitions(),
        observations=(
            obs("p1", "historical_performance", 1.0, "future", when=CUTOFF),
            obs("p1", "raw_speed", 1.0, "restricted", rights="UNASSESSED", unit="m/s"),
            obs("p1", "raw_speed", 2.0, "other-provider", provider="other", unit="m/s"),
        ),
    )
    reasons = {item.reason for item in snapshot.exclusions}
    assert "POST_CUTOFF_OR_UNVERIFIED" in reasons
    assert "RIGHTS_NOT_APPROVED" in reasons
    assert "IDENTITY_LINK_REQUIRED" in reasons
    assert "historical_performance" not in snapshot.records["p1"]
    assert "raw_speed" not in snapshot.records["p1"]
    assert "p1:historical_performance" in snapshot.critical_missing


def test_cross_provider_join_requires_reconciled_identity_and_units_match() -> None:
    snapshot = generate_feature_snapshot(
        race_id="race-1", code="THOROUGHBRED", cutoff=CUTOFF, participant_ids=("p1", "p2"), definitions=definitions(),
        observations=(
            obs("p1", "raw_speed", 10.0, "one", provider="a", unit="m/s", identity_link="link-1", evidence="RECONCILED"),
            obs("p1", "raw_speed", 12.0, "two", provider="b", unit="m/s", identity_link="link-1", evidence="RECONCILED"),
            obs("p2", "raw_speed", 11.0, "bad-unit", unit="score"),
        ),
    )
    assert not any(item.reason == "IDENTITY_LINK_REQUIRED" for item in snapshot.exclusions)
    assert any(item.reason == "UNIT_MISMATCH" for item in snapshot.exclusions)
    assert any(item.reason == "PROVIDER_FEATURE_CONFLICT" for item in snapshot.exclusions)
    assert "raw_speed" not in snapshot.records["p1"]


def test_leakage_canary_post_race_value_cannot_change_snapshot() -> None:
    future_one = obs("p1", "historical_performance", 1.0, "future", when=CUTOFF + timedelta(minutes=1))
    future_two = obs("p1", "historical_performance", 999.0, "future", when=CUTOFF + timedelta(minutes=1))
    first = generate_feature_snapshot(race_id="race-1", code="THOROUGHBRED", cutoff=CUTOFF, participant_ids=("p1",), definitions=definitions(), observations=(future_one,))
    second = generate_feature_snapshot(race_id="race-1", code="THOROUGHBRED", cutoff=CUTOFF, participant_ids=("p1",), definitions=definitions(), observations=(future_two,))
    assert first.snapshot_hash == second.snapshot_hash
    assert first.critical_missing == ("p1:historical_performance",)
    assert "historical_performance" not in first.records["p1"]
