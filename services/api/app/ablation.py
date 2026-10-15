"""Synthetic-only feature/provider ablation reports with no promotion authority."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
import hashlib
import json

from app.metrics import EvaluationRecord, evaluate_records


def _utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _validate_records(
    records: Sequence[EvaluationRecord],
    *,
    expected_ids: set[str],
    holdout_start: datetime,
    holdout_end: datetime,
    label: str,
) -> dict[str, EvaluationRecord]:
    if not records:
        raise ValueError(f"{label} records cannot be empty")
    indexed: dict[str, EvaluationRecord] = {}
    for record in records:
        if record.race_id in indexed:
            raise ValueError(f"{label} records contain duplicate race IDs")
        observed_at = _utc(record.observed_at, "observed_at")
        if not _utc(holdout_start, "holdout_start") <= observed_at < _utc(holdout_end, "holdout_end"):
            raise ValueError(f"{label} record falls outside the chronological holdout")
        if record.race_id not in expected_ids:
            raise ValueError(f"{label} record is outside the expected race set")
        indexed[record.race_id] = record
    return indexed


def build_ablation_report(
    baseline_records: Sequence[EvaluationRecord],
    incremental_records: Sequence[EvaluationRecord],
    *,
    study_id: str,
    feature_family: str,
    provider_id: str,
    expected_race_ids: Sequence[str],
    holdout_start: datetime,
    holdout_end: datetime,
    bootstrap_seed: int = 20260115,
    bootstrap_repetitions: int = 1000,
) -> dict[str, object]:
    """Compare two models on the same chronological, synthetic holdout."""

    if not study_id.strip() or not feature_family.strip() or not provider_id.strip():
        raise ValueError("ablation identity fields are required")
    expected = set(expected_race_ids)
    if not expected or len(expected) != len(tuple(expected_race_ids)):
        raise ValueError("expected_race_ids must be non-empty and unique")
    start = _utc(holdout_start, "holdout_start")
    end = _utc(holdout_end, "holdout_end")
    if end <= start:
        raise ValueError("holdout_end must be after holdout_start")
    baseline = _validate_records(baseline_records, expected_ids=expected, holdout_start=start, holdout_end=end, label="baseline")
    incremental = _validate_records(incremental_records, expected_ids=expected, holdout_start=start, holdout_end=end, label="incremental")
    if set(baseline) != set(incremental):
        raise ValueError("baseline and incremental records must score the same races")
    for race_id in sorted(baseline):
        left = baseline[race_id]
        right = incremental[race_id]
        if (left.winner_entry_id, left.code, left.observed_at) != (right.winner_entry_id, right.code, right.observed_at):
            raise ValueError("baseline and incremental records must share race identity and outcome")

    baseline_report = evaluate_records(baseline_records, bootstrap_seed=bootstrap_seed, bootstrap_repetitions=bootstrap_repetitions)
    incremental_report = evaluate_records(incremental_records, bootstrap_seed=bootstrap_seed, bootstrap_repetitions=bootstrap_repetitions)
    body: dict[str, object] = {
        "schema_version": "ablation-report-v1",
        "study_id": study_id,
        "feature_family": feature_family,
        "provider_id": provider_id,
        "data_mode": "SYNTHETIC_ONLY",
        "validated_claim": False,
        "holdout": {
            "start": start.isoformat().replace("+00:00", "Z"),
            "end": end.isoformat().replace("+00:00", "Z"),
            "expected_races": sorted(expected),
        },
        "coverage": {
            "expected_races": len(expected),
            "baseline_scored": len(baseline),
            "incremental_scored": len(incremental),
            "baseline_fraction": len(baseline) / len(expected),
            "incremental_fraction": len(incremental) / len(expected),
        },
        "baseline": baseline_report,
        "incremental": incremental_report,
        "delta": {
            "log_loss": incremental_report["log_loss"] - baseline_report["log_loss"],
            "brier": incremental_report["brier"] - baseline_report["brier"],
        },
        "status": "IMPLEMENTATION_METRICS_SYNTHETIC_ONLY",
        "promotion": "HOLD",
        "promotion_reason": "ablation evidence cannot promote a model without calibration, independent assurance and owner approval",
    }
    body["report_hash"] = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()
    return body


def verify_ablation_report(report: dict[str, object]) -> None:
    """Verify the report hash and the non-promotion safety markers."""

    report_hash = report.get("report_hash")
    if not isinstance(report_hash, str):
        raise ValueError("ablation report hash is required")
    body = {key: value for key, value in report.items() if key != "report_hash"}
    expected_hash = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()
    if report_hash != expected_hash:
        raise ValueError("ablation report hash mismatch")
    if report.get("data_mode") != "SYNTHETIC_ONLY" or report.get("validated_claim") is not False or report.get("promotion") != "HOLD":
        raise ValueError("ablation report safety markers are invalid")
