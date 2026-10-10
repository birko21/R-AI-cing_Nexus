from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.backup_controls import RetentionRecord, create_backup_manifest, migration_rollback_steps, plan_retention, restore_to_isolated, verify_backup_manifest


NOW = datetime(2026, 1, 15, tzinfo=timezone.utc)


def test_backup_manifest_restore_and_hash_verification_are_isolated(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "restore"
    source.mkdir()
    (source / "fixture.json").write_text('{"fictional": true}\n', encoding="utf-8")
    entries = create_backup_manifest(source, ("fixture.json",))
    assert verify_backup_manifest(source, entries) == ()
    assert restore_to_isolated(source, destination, entries) == ("fixture.json",)
    assert verify_backup_manifest(destination, entries) == ()
    (source / "fixture.json").write_text("tampered\n", encoding="utf-8")
    assert verify_backup_manifest(source, entries) == ("fixture.json",)


def test_retention_plan_only_returns_expired_restricted_records_and_never_deletes() -> None:
    records = (
        RetentionRecord("restricted-expired", NOW - timedelta(days=4), NOW - timedelta(days=1), "RESTRICTED"),
        RetentionRecord("approved-expired", NOW - timedelta(days=4), NOW - timedelta(days=1), "APPROVED"),
        RetentionRecord("restricted-current", NOW, NOW + timedelta(days=1), "RESTRICTED"),
    )
    assert plan_retention(records, as_of=NOW) == ("restricted-expired",)


def test_backup_paths_and_rollback_plan_fail_closed() -> None:
    with pytest.raises(ValueError, match="existing file"):
        create_backup_manifest(Path("."), ("missing-file",))
    assert migration_rollback_steps()[0] == "record_current_revision"
    with pytest.raises(ValueError, match="timezone-aware"):
        plan_retention((), as_of=datetime(2026, 1, 15))
