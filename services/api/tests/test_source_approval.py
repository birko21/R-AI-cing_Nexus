from __future__ import annotations

import pytest

from app.source_approval import (
    REQUIRED_APPROVALS,
    SourceApprovalRecord,
    UnavailableSourceStub,
    evaluate_source_approval,
    evaluate_tiered_source_approval,
)


def test_missing_provider_evidence_is_explicitly_blocked() -> None:
    checkpoint = evaluate_source_approval(SourceApprovalRecord("provider-pending"))

    assert checkpoint.status == "BLOCKED_EXTERNAL_DEPENDENCY"
    assert checkpoint.missing_requirements == REQUIRED_APPROVALS
    assert UnavailableSourceStub(checkpoint).request("GET_RACES")["status"] == "NOT_AVAILABLE"


def test_partial_provider_evidence_remains_blocked_without_secret_storage() -> None:
    checkpoint = evaluate_source_approval(
        SourceApprovalRecord("provider-pending", written_rights="rights-record-1", display_permission="display-record-1")
    )

    assert checkpoint.status == "BLOCKED_EXTERNAL_DEPENDENCY"
    assert "credential_policy" in checkpoint.missing_requirements
    assert "retention_terms" in checkpoint.missing_requirements


def test_complete_record_can_become_approved_without_containing_credentials() -> None:
    checkpoint = evaluate_source_approval(
        SourceApprovalRecord(
            "provider-approved",
            written_rights="rights-record-1",
            credential_policy="credential-policy-1",
            retention_terms="retention-record-1",
            model_training_permission="model-use-record-1",
            display_permission="display-record-1",
            reconciliation_report="reconciliation-1",
        )
    )

    assert checkpoint.status == "APPROVED"
    assert checkpoint.missing_requirements == ()


def test_unavailable_stub_cannot_be_constructed_for_approved_source() -> None:
    checkpoint = evaluate_source_approval(SourceApprovalRecord("provider-pending"))
    checkpoint = checkpoint.__class__(checkpoint.source_id, "APPROVED", (), "incorrect")
    with pytest.raises(ValueError, match="blocked"):
        UnavailableSourceStub(checkpoint)


def test_read_and_diagnostic_tiers_do_not_imply_historical_model_rights() -> None:
    record = SourceApprovalRecord(
        "punters-edge",
        approved_operations=("GET_RESULTS",),
        approved_codes=("THOROUGHBRED",),
        approval_tier="EPHEMERAL_READ_ONLY_DIAGNOSTIC",
        account_entitlement_evidence="account-plan-record",
        credential_custodian="owner",
        quota_ceiling="6 requests",
        kill_switch_reference="diagnostics-off",
    )

    diagnostic = evaluate_tiered_source_approval(
        record, required_tier="EPHEMERAL_READ_ONLY_DIAGNOSTIC", operation="GET_RESULTS", code="THOROUGHBRED",
    )
    historical = evaluate_tiered_source_approval(
        record, required_tier="HISTORICAL_RETENTION_AND_MODEL_TRAINING", operation="GET_RESULTS", code="THOROUGHBRED",
    )

    assert diagnostic.status == "APPROVED"
    assert historical.status == "BLOCKED_EXTERNAL_DEPENDENCY"
    assert "model_training_permission" in historical.missing_requirements
