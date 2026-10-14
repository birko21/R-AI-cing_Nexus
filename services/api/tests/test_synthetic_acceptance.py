from app.synthetic_acceptance import run_synthetic_vertical_proof


def test_synthetic_vertical_proof_exercises_ingestion_forecast_archive_and_hold() -> None:
    result = run_synthetic_vertical_proof()

    assert result["status"] == "PASS"
    assert result["ingestion"]["first_run"]["envelopes_persisted"] == 3
    assert result["ingestion"]["replay_run"]["envelopes_skipped"] == 3
    assert result["ingestion"]["stored_quarantines"] == 0
    assert result["forecast"]["status"] == "READY"
    assert result["forecast"]["archive_replay_matches"] is True
    assert result["release_gate"]["status"] == "LOCAL_SYNTHETIC_ONLY_HOLD"
    assert result["release_gate"]["activation_authority"] == "NONE"
