from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.backup_controls import RetentionRecord, create_backup_manifest, migration_rollback_steps, plan_retention, verify_backup_manifest  # noqa: E402


OUTPUT = ROOT / "docs" / "evidence" / "ril-059" / "backup-restore-transcript.json"
NOW = datetime(2026, 1, 15, tzinfo=timezone.utc)


def build_fixture() -> dict[str, object]:
    entries = create_backup_manifest(ROOT, ("fixtures/synthetic/manifest.json", "fixtures/synthetic/research_tools_v1.json"))
    retention = plan_retention((RetentionRecord("restricted-expired", NOW - timedelta(days=4), NOW - timedelta(days=1), "RESTRICTED"),), as_of=NOW)
    return {
        "schema_version": "backup-restore-v1", "manifest": [entry.__dict__ for entry in entries],
        "checksum_failures_before_restore": list(verify_backup_manifest(ROOT, entries)),
        "retention_delete_plan": list(retention), "migration_rollback_steps": list(migration_rollback_steps()),
        "isolated_restore": True, "deletion_performed": False, "fictional": True,
        "watermark": "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE",
        "note": "Synthetic backup/restore and retention-plan evidence; no production database or user data was modified.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    expected = build_fixture()
    if args.write:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not args.output.exists() or json.loads(args.output.read_text(encoding="utf-8")) != expected:
        raise SystemExit("BACKUP FIXTURE CHECK FAILED: generated content differs")
    print(f"BACKUP FIXTURE VALID: files={len(expected['manifest'])} retention_candidates={len(expected['retention_delete_plan'])} deletion={expected['deletion_performed']}")


if __name__ == "__main__":
    main()
