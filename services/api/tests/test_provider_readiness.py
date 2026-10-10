from app.provider_readiness import build_provider_readiness_report


def test_provider_readiness_is_evidence_backed_and_external_connectivity_stays_disabled() -> None:
    report = build_provider_readiness_report()

    assert report["external_connectivity"] == "DISABLED"
    assert report["available_and_approved"] == []
    verdicts = {row["code"]: row["status"] for row in report["code_verdicts"]}
    assert verdicts == {
        "THOROUGHBRED": "TECHNICALLY_AVAILABLE_RIGHTS_PENDING",
        "HARNESS": "INSUFFICIENT_FEATURE_COVERAGE",
        "GREYHOUND": "INSUFFICIENT_FEATURE_COVERAGE",
    }
    assert len(report["provider_code_verdicts"]) == 12
