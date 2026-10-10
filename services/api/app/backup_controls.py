"""Safe backup/restore, checksum and retention-plan controls for permitted data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
from pathlib import Path
import shutil
from typing import Literal


PermittedMode = Literal["SYNTHETIC_ONLY", "SCRAPED_PUBLIC"]


@dataclass(frozen=True)
class BackupEntry:
    relative_path: str
    sha256: str
    size_bytes: int
    data_mode: PermittedMode


@dataclass(frozen=True)
class RetentionRecord:
    record_id: str
    observed_at: datetime
    expires_at: datetime
    rights_state: str


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_backup_manifest(root: Path, relative_paths: tuple[str, ...], *, data_mode: PermittedMode = "SYNTHETIC_ONLY") -> tuple[BackupEntry, ...]:
    entries: list[BackupEntry] = []
    for relative in relative_paths:
        path = (root / relative).resolve()
        if not path.is_file() or root.resolve() not in path.parents:
            raise ValueError(f"backup source must be an existing file inside root: {relative}")
        entries.append(BackupEntry(relative, _digest(path), path.stat().st_size, data_mode))
    return tuple(entries)


def verify_backup_manifest(root: Path, entries: tuple[BackupEntry, ...]) -> tuple[str, ...]:
    failures: list[str] = []
    for entry in entries:
        path = (root / entry.relative_path).resolve()
        if not path.is_file() or _digest(path) != entry.sha256 or path.stat().st_size != entry.size_bytes:
            failures.append(entry.relative_path)
    return tuple(failures)


def restore_to_isolated(source_root: Path, destination_root: Path, entries: tuple[BackupEntry, ...]) -> tuple[str, ...]:
    """Copy only manifest entries to a caller-provided isolated destination."""

    destination_root.mkdir(parents=True, exist_ok=True)
    restored: list[str] = []
    for entry in entries:
        source = (source_root / entry.relative_path).resolve()
        target = (destination_root / entry.relative_path).resolve()
        if source_root.resolve() not in source.parents or destination_root.resolve() not in target.parents:
            raise ValueError("restore paths must remain inside their explicit roots")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        restored.append(entry.relative_path)
    return tuple(restored)


def plan_retention(records: tuple[RetentionRecord, ...], *, as_of: datetime) -> tuple[str, ...]:
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("as_of must be timezone-aware")
    return tuple(record.record_id for record in records if record.expires_at <= as_of and record.rights_state in {"RESTRICTED", "REJECTED"})


def migration_rollback_steps() -> tuple[str, ...]:
    return ("record_current_revision", "apply_migration_in_isolated_database", "run_checksum_and_fixture_checks", "downgrade_one_revision", "verify_previous_revision", "promote_only_after_owner_review")
