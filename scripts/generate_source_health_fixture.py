from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.capabilities import SourceCapabilityPolicy  # noqa: E402
from app.source_health import HealthObservation, SourceHealthMonitor  # noqa: E402


OUTPUT = ROOT / "fixtures" / "synthetic" / "source_health_v1.json"
NOW = datetime(2026, 1, 15, 12, tzinfo=timezone.utc)


def observation(schema_version: str) -> HealthObservation:
    return HealthObservation(
        source_id="synthetic-health-fixture", checked_at=NOW, expected_schema_version="race-v1",
        observed_schema_version=schema_version, last_success_at=NOW - timedelta(minutes=5),
        latest_data_at=NOW - timedelta(hours=1), expected_coverage=frozenset({"meetings", "races", "entries", "results"}),
        observed_coverage=frozenset({"meetings", "races", "entries", "results"}), quota_remaining=10,
    )


def build_fixture() -> dict[str, object]:
    monitor = SourceHealthMonitor()
    healthy = monitor.evaluate(observation("race-v1"))
    drifted = monitor.evaluate(observation("race-v2"))
    policy = SourceCapabilityPolicy(
        source_id="synthetic-health-fixture", data_mode="SYNTHETIC_ONLY", rights_state="SYNTHETIC",
        approved_capabilities=frozenset({"STORE", "DISPLAY", "EXPORT"}),
    )
    disabled = monitor.apply_kill_switch(policy, drifted)
    return {
        "schema_version": "source-health-v1",
        "healthy": healthy.to_dict(),
        "schema_drift_failure": drifted.to_dict(),
        "post_kill_switch": {
            "enabled": disabled.enabled,
            "kill_switch_reason": disabled.kill_switch_reason,
        },
        "fictional": True,
        "watermark": "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE",
        "note": "Failure-injection dashboard evidence only; historical records are not mutated.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    expected = build_fixture()
    if args.write:
        args.output.write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not args.output.exists() or json.loads(args.output.read_text(encoding="utf-8")) != expected:
        raise SystemExit("SOURCE HEALTH FIXTURE CHECK FAILED: generated content differs")
    print(f"SOURCE HEALTH FIXTURE VALID: healthy={expected['healthy']['status']} failure={expected['schema_drift_failure']['status']}")


if __name__ == "__main__":
    main()
