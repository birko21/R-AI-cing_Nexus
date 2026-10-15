from dataclasses import replace
from datetime import datetime, timezone

import pytest

from app.provider_evidence import ProviderEvidenceRecord, ProviderEvidenceRegistry


NOW = datetime(2026, 1, 15, tzinfo=timezone.utc)


def record(evidence_id: str = "evidence-1") -> ProviderEvidenceRecord:
    return ProviderEvidenceRecord(
        evidence_id=evidence_id,
        provider_id="synthetic-fixture",
        capability="GET_RACES",
        source_reference="docs/models/PROVIDER_ADAPTER_CONTRACT.md",
        observed_at=NOW,
        evidence_status="OBSERVED",
        data_mode="SYNTHETIC_ONLY",
        rights_state="SYNTHETIC",
        notes="offline contract evidence",
    )


def test_provider_evidence_is_typed_append_only_and_has_no_activation_authority() -> None:
    registry = ProviderEvidenceRegistry()
    registry.register(record())
    registry.register(record())

    snapshot = registry.snapshot()

    assert snapshot["activation_authority"] == "NONE"
    assert snapshot["records"] == [record().to_dict()]

    with pytest.raises(ValueError, match="immutable"):
        registry.register(replace(record(), notes="changed"))


def test_provider_evidence_requires_aware_time_and_identity() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        ProviderEvidenceRecord(**{**record().__dict__, "observed_at": datetime(2026, 1, 15)})
    with pytest.raises(ValueError, match="identity"):
        ProviderEvidenceRecord(**{**record().__dict__, "provider_id": " "})
