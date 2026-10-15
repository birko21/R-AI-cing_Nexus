"""Explicit runtime controls for synthetic and live provider modes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import os
from typing import Literal


DataMode = Literal["SYNTHETIC_ONLY", "SCRAPED_PUBLIC", "LICENSED"]
PersistenceMode = Literal["synthetic", "postgres"]


@dataclass(frozen=True)
class RuntimeConfig:
    data_mode: DataMode
    persistence: PersistenceMode
    live_provider: str | None
    live_operations: tuple[str, ...]
    live_codes: tuple[str, ...]
    read_only: bool

    @property
    def live_enabled(self) -> bool:
        return self.data_mode == "LICENSED"

    def validate(self) -> None:
        if self.live_enabled and self.persistence != "postgres":
            raise RuntimeError("LICENSED data mode requires NEXUS_API_PERSISTENCE=postgres")
        if self.live_enabled and not self.read_only:
            raise RuntimeError("live provider mode is read-only; wagering is not supported")
        if self.live_enabled and not self.live_provider:
            raise RuntimeError("LICENSED data mode requires NEXUS_LIVE_PROVIDER")
        if self.live_enabled and not self.live_operations:
            raise RuntimeError("LICENSED data mode requires NEXUS_LIVE_OPERATIONS")
        if self.live_enabled and not self.live_codes:
            raise RuntimeError("LICENSED data mode requires NEXUS_LIVE_CODES")


def _csv(environ: Mapping[str, str], name: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in environ.get(name, "").split(",") if item.strip())


def load_runtime_config(*, environ: Mapping[str, str] | None = None) -> RuntimeConfig:
    values = os.environ if environ is None else environ
    persistence_value = values.get("NEXUS_API_PERSISTENCE", "synthetic").strip().lower()
    if persistence_value not in {"synthetic", "postgres"}:
        raise RuntimeError("NEXUS_API_PERSISTENCE must be synthetic or postgres")

    mode_value = values.get("NEXUS_DATA_MODE", "").strip().upper()
    if not mode_value:
        if values.get("APP_ENV", "development").strip().lower() not in {"development", "test", "testing"}:
            raise RuntimeError("NEXUS_DATA_MODE must be explicit outside development and test environments")
        mode_value = "LICENSED" if persistence_value == "postgres" else "SYNTHETIC_ONLY"
    if mode_value not in {"SYNTHETIC_ONLY", "SCRAPED_PUBLIC", "LICENSED"}:
        raise RuntimeError("NEXUS_DATA_MODE must be SYNTHETIC_ONLY, SCRAPED_PUBLIC or LICENSED")

    config = RuntimeConfig(
        data_mode=mode_value,  # type: ignore[arg-type]
        persistence=persistence_value,  # type: ignore[arg-type]
        live_provider=values.get("NEXUS_LIVE_PROVIDER", "").strip() or None,
        live_operations=_csv(values, "NEXUS_LIVE_OPERATIONS"),
        live_codes=_csv(values, "NEXUS_LIVE_CODES"),
        read_only=values.get("NEXUS_LIVE_READ_ONLY", "true").strip().lower() in {"1", "true", "yes", "on"},
    )
    config.validate()
    return config
