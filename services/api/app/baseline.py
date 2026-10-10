"""Deterministic B0 uniform baseline for synthetic, pre-race fields."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from typing import Literal


WATERMARK = "FICTIONAL_SYNTHETIC_DO_NOT_TREAT_AS_LIVE"
MODEL_ID = "B0_UNIFORM"
MODEL_VERSION = "b0-uniform-v1"
MODEL_STATUS = "ILLUSTRATIVE_NOT_VALIDATED"
VALID_FIELD_STATES = frozenset({"ACCEPTANCES", "FINAL_FIELDS", "OFFICIAL"})
ACTIVE_STATUS = "ACTIVE"

ForecastStatus = Literal["READY", "ABSTAIN"]


@dataclass(frozen=True)
class BaselineRunner:
    entry_id: str
    number: int
    status: str = ACTIVE_STATUS
    eligible: bool = True
    coupled_group: str | None = None


@dataclass(frozen=True)
class BaselineRace:
    race_id: str
    code: str
    field_revision: str
    field_status: str
    runners: tuple[BaselineRunner, ...]
    data_mode: str = "SYNTHETIC_ONLY"


@dataclass(frozen=True)
class RunnerProbability:
    entry_id: str
    number: int
    probability: float | None


@dataclass(frozen=True)
class B0Forecast:
    forecast_id: str
    race_id: str
    code: str
    field_revision: str
    field_status: str
    cutoff: str
    model_id: str
    model_version: str
    model_status: str
    data_mode: str
    manifest_checksum: str
    status: ForecastStatus
    runners: tuple[RunnerProbability, ...]
    abstention_reason: str | None
    diagnostics: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            **asdict(self),
            "runners": [asdict(runner) for runner in self.runners],
            "diagnostics": list(self.diagnostics),
        }


def _normalise_cutoff(cutoff: datetime) -> str:
    if cutoff.tzinfo is None or cutoff.utcoffset() is None:
        raise ValueError("cutoff must be timezone-aware")
    return cutoff.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _forecast_id(race: BaselineRace, cutoff: str, manifest_checksum: str) -> str:
    payload = json.dumps(
        {
            "race_id": race.race_id,
            "field_revision": race.field_revision,
            "cutoff": cutoff,
            "model_id": MODEL_ID,
            "model_version": MODEL_VERSION,
            "manifest_checksum": manifest_checksum,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"b0-{hashlib.sha256(payload).hexdigest()[:16]}"


def _abstain(
    race: BaselineRace,
    *,
    cutoff: str,
    manifest_checksum: str,
    reason: str,
    diagnostics: tuple[str, ...] = (),
) -> B0Forecast:
    return B0Forecast(
        forecast_id=_forecast_id(race, cutoff, manifest_checksum),
        race_id=race.race_id,
        code=race.code,
        field_revision=race.field_revision,
        field_status=race.field_status,
        cutoff=cutoff,
        model_id=MODEL_ID,
        model_version=MODEL_VERSION,
        model_status=MODEL_STATUS,
        data_mode=race.data_mode,
        manifest_checksum=manifest_checksum,
        status="ABSTAIN",
        runners=tuple(),
        abstention_reason=reason,
        diagnostics=diagnostics,
    )


def build_b0_forecast(
    race: BaselineRace,
    *,
    cutoff: datetime,
    manifest_checksum: str,
    unsupported_outcome: str | None = None,
) -> B0Forecast:
    """Build a uniform forecast or fail closed with an explicit reason.

    Only active, eligible, non-coupled runners in a valid field receive a
    probability. Scratchings and reserves are intentionally excluded.
    """

    if not manifest_checksum:
        raise ValueError("manifest_checksum is required")
    cutoff_text = _normalise_cutoff(cutoff)
    if race.data_mode != "SYNTHETIC_ONLY":
        return _abstain(race, cutoff=cutoff_text, manifest_checksum=manifest_checksum, reason="UNSUPPORTED_DATA_MODE")
    if unsupported_outcome:
        return _abstain(
            race,
            cutoff=cutoff_text,
            manifest_checksum=manifest_checksum,
            reason="UNSUPPORTED_OUTCOME",
            diagnostics=(unsupported_outcome,),
        )
    if race.field_status not in VALID_FIELD_STATES:
        return _abstain(race, cutoff=cutoff_text, manifest_checksum=manifest_checksum, reason="FIELD_NOT_VALID")
    if not race.runners:
        return _abstain(race, cutoff=cutoff_text, manifest_checksum=manifest_checksum, reason="INCOMPLETE_FIELD")
    if len({runner.entry_id for runner in race.runners}) != len(race.runners):
        return _abstain(race, cutoff=cutoff_text, manifest_checksum=manifest_checksum, reason="DUPLICATE_ENTRY_ID")
    if any(runner.coupled_group for runner in race.runners):
        return _abstain(race, cutoff=cutoff_text, manifest_checksum=manifest_checksum, reason="COUPLED_ENTRY")

    active = tuple(runner for runner in race.runners if runner.status == ACTIVE_STATUS and runner.eligible)
    if not active:
        return _abstain(race, cutoff=cutoff_text, manifest_checksum=manifest_checksum, reason="NO_ACTIVE_ELIGIBLE_RUNNERS")
    probability = 1.0 / len(active)
    if not math.isfinite(probability):
        return _abstain(race, cutoff=cutoff_text, manifest_checksum=manifest_checksum, reason="NONFINITE_PROBABILITY")
    return B0Forecast(
        forecast_id=_forecast_id(race, cutoff_text, manifest_checksum),
        race_id=race.race_id,
        code=race.code,
        field_revision=race.field_revision,
        field_status=race.field_status,
        cutoff=cutoff_text,
        model_id=MODEL_ID,
        model_version=MODEL_VERSION,
        model_status=MODEL_STATUS,
        data_mode=race.data_mode,
        manifest_checksum=manifest_checksum,
        status="READY",
        runners=tuple(RunnerProbability(runner.entry_id, runner.number, probability) for runner in active),
        abstention_reason=None,
        diagnostics=(f"UNIFORM_ACTIVE_ELIGIBLE_N={len(active)}",),
    )

