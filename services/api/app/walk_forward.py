"""Chronological train/calibration/test splitting with overlap guards."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
from collections.abc import Iterable
from typing import Literal


SplitMode = Literal["EXPANDING", "ROLLING"]


@dataclass(frozen=True)
class RaceObservation:
    race_id: str
    scheduled_at: datetime
    code: str


@dataclass(frozen=True)
class WalkForwardFold:
    fold_id: str
    mode: SplitMode
    training_start: str
    training_end: str
    calibration_start: str
    calibration_end: str
    test_start: str
    test_end: str
    training_race_ids: tuple[str, ...]
    calibration_race_ids: tuple[str, ...]
    test_race_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        for key in ("training_race_ids", "calibration_race_ids", "test_race_ids"):
            payload[key] = list(payload[key])
        return payload


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("race timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)


def _text(value: datetime) -> str:
    return _utc(value).isoformat().replace("+00:00", "Z")


def build_walk_forward_splits(
    races: Iterable[RaceObservation],
    *,
    initial_train_end: datetime,
    calibration_duration: timedelta,
    test_duration: timedelta,
    step: timedelta,
    mode: SplitMode = "EXPANDING",
    initial_train_start: datetime | None = None,
    rolling_train_duration: timedelta | None = None,
) -> tuple[WalkForwardFold, ...]:
    """Create chronological half-open folds: train, calibration, then test."""

    observations = tuple(races)
    if mode not in {"EXPANDING", "ROLLING"}:
        raise ValueError("mode must be EXPANDING or ROLLING")
    if calibration_duration <= timedelta(0) or test_duration <= timedelta(0) or step <= timedelta(0):
        raise ValueError("window durations and step must be positive")
    if mode == "ROLLING" and (rolling_train_duration is None or rolling_train_duration <= timedelta(0)):
        raise ValueError("rolling mode requires a positive rolling_train_duration")
    if len({observation.race_id for observation in observations}) != len(observations):
        raise ValueError("race IDs must be unique")
    normalized = tuple(sorted((RaceObservation(item.race_id, _utc(item.scheduled_at), item.code) for item in observations), key=lambda item: (item.scheduled_at, item.race_id)))
    if not normalized:
        return tuple()
    first = _utc(initial_train_start) if initial_train_start else normalized[0].scheduled_at
    cursor = _utc(initial_train_end)
    last = normalized[-1].scheduled_at
    folds: list[WalkForwardFold] = []
    fold_number = 1
    while cursor + calibration_duration + test_duration <= last + step:
        training_start = cursor - rolling_train_duration if mode == "ROLLING" else first
        calibration_start = cursor
        calibration_end = calibration_start + calibration_duration
        test_start = calibration_end
        test_end = test_start + test_duration
        training_ids = tuple(item.race_id for item in normalized if training_start <= item.scheduled_at < cursor)
        calibration_ids = tuple(item.race_id for item in normalized if calibration_start <= item.scheduled_at < calibration_end)
        test_ids = tuple(item.race_id for item in normalized if test_start <= item.scheduled_at < test_end)
        groups = (set(training_ids), set(calibration_ids), set(test_ids))
        if groups[0] & groups[1] or groups[0] & groups[2] or groups[1] & groups[2]:
            raise ValueError("walk-forward fold has overlapping race IDs")
        folds.append(WalkForwardFold(
            fold_id=f"fold-{fold_number:03d}", mode=mode,
            training_start=_text(training_start), training_end=_text(cursor),
            calibration_start=_text(calibration_start), calibration_end=_text(calibration_end),
            test_start=_text(test_start), test_end=_text(test_end),
            training_race_ids=training_ids, calibration_race_ids=calibration_ids, test_race_ids=test_ids,
        ))
        fold_number += 1
        cursor += step
    return tuple(folds)


def split_manifest(folds: Iterable[WalkForwardFold], *, data_mode: str = "SYNTHETIC_ONLY") -> dict[str, object]:
    records = [fold.to_dict() for fold in folds]
    body = {"schema_version": "walk-forward-v1", "mode": records[0]["mode"] if records else None, "folds": records, "data_mode": data_mode}
    body["manifest_hash"] = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return body

