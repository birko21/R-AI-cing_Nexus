"""Experimental harness position scenarios with explicit capability states."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Literal


ScenarioStatus = Literal["EXPERIMENTAL", "NOT_AVAILABLE"]


@dataclass(frozen=True)
class HarnessFact:
    participant_id: str
    observed_at: datetime
    source_receipt_id: str
    start_type: str | None = None
    row: int | None = None
    barrier: int | None = None
    pacing: str | None = None
    sectional_time: float | None = None
    running_line: str | None = None


@dataclass(frozen=True)
class ScenarioValue:
    value: str | float | None
    missing: bool
    missing_reason: str | None
    source_receipt_ids: tuple[str, ...]


@dataclass(frozen=True)
class HarnessScenario:
    schema_version: str
    scenario_id: str
    participant_id: str
    cutoff: str
    status: ScenarioStatus
    data_mode: str
    inputs: dict[str, ScenarioValue]
    hypotheses: tuple[str, ...]
    included_receipt_ids: tuple[str, ...]
    excluded_future_receipt_ids: tuple[str, ...]
    scenario_label: str
    snapshot_hash: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["inputs"] = {key: {**asdict(value), "source_receipt_ids": list(value.source_receipt_ids)} for key, value in self.inputs.items()}
        payload["included_receipt_ids"] = list(self.included_receipt_ids)
        payload["excluded_future_receipt_ids"] = list(self.excluded_future_receipt_ids)
        payload["hypotheses"] = list(self.hypotheses)
        return payload


def build_harness_scenario(*, scenario_id: str, participant_id: str, cutoff: datetime, facts: tuple[HarnessFact, ...], data_mode: str = "SYNTHETIC_ONLY") -> HarnessScenario:
    if cutoff.tzinfo is None or cutoff.utcoffset() is None:
        raise ValueError("cutoff must be timezone-aware")
    if data_mode not in {"SYNTHETIC_ONLY", "SCRAPED_PUBLIC"}:
        raise ValueError("harness scenario data_mode is unsupported")
    cutoff_iso = cutoff.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    included = tuple(sorted((fact for fact in facts if fact.participant_id == participant_id and fact.observed_at < cutoff), key=lambda fact: fact.observed_at))
    excluded = tuple(sorted((fact for fact in facts if fact.participant_id == participant_id and fact.observed_at >= cutoff), key=lambda fact: fact.observed_at))
    receipts = tuple(fact.source_receipt_id for fact in included)
    future_receipts = tuple(fact.source_receipt_id for fact in excluded)
    names = ("start_type", "row", "barrier", "pacing", "sectional_time", "running_line")
    inputs: dict[str, ScenarioValue] = {}
    if not included:
        inputs = {name: ScenarioValue(None, True, "NO_PRE_CUTOFF_SUPPORT", ()) for name in names}
        hypotheses: tuple[str, ...] = ()
        status: ScenarioStatus = "NOT_AVAILABLE"
    else:
        latest = included[-1]
        for name in names:
            value = getattr(latest, name)
            inputs[name] = ScenarioValue(value, value is None, None if value is not None else f"MISSING_{name.upper()}", (latest.source_receipt_id,) if value is not None else receipts)
        hypotheses_list: list[str] = []
        if latest.start_type and latest.pacing:
            hypotheses_list.append(f"EXPERIMENTAL_RUNNING_LINE: {latest.start_type} with {latest.pacing} pacing")
        if latest.row is not None or latest.barrier is not None:
            hypotheses_list.append("EXPERIMENTAL_POSITION: row/barrier may alter the descriptive position scenario")
        hypotheses = tuple(hypotheses_list)
        status = "EXPERIMENTAL"
    body = {
        "schema_version": "harness-scenarios-v1", "scenario_id": scenario_id, "participant_id": participant_id,
        "cutoff": cutoff_iso, "status": status, "data_mode": data_mode,
        "inputs": {key: asdict(value) for key, value in inputs.items()}, "hypotheses": list(hypotheses),
        "included_receipt_ids": list(receipts), "excluded_future_receipt_ids": list(future_receipts),
        "scenario_label": "EXPERIMENTAL_UNCALIBRATED",
    }
    digest = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return HarnessScenario("harness-scenarios-v1", scenario_id, participant_id, cutoff_iso, status, data_mode, inputs, hypotheses, receipts, future_receipts, "EXPERIMENTAL_UNCALIBRATED", digest)
