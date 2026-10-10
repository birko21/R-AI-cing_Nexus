"""Evidence-backed provider/code readiness verdicts for the RIL-061 gate."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


ReadinessStatus = Literal[
    "AVAILABLE_AND_APPROVED", "TECHNICALLY_AVAILABLE_RIGHTS_PENDING", "INSUFFICIENT_HISTORY",
    "INSUFFICIENT_FEATURE_COVERAGE", "NOT_AVAILABLE",
]
PROVIDERS = ("FormFav", "PuntersEdge", "Krok Odds", "Betfair Exchange")
CODES = ("THOROUGHBRED", "HARNESS", "GREYHOUND")


@dataclass(frozen=True)
class ProviderCodeReadiness:
    provider: str
    code: str
    status: ReadinessStatus
    evidence: tuple[str, ...]
    blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CodeReadiness:
    code: str
    status: ReadinessStatus
    supporting_providers: tuple[str, ...]
    evidence: tuple[str, ...]
    blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_provider_readiness_report() -> dict[str, object]:
    """Return the current verdict without contacting any provider."""

    rows: list[ProviderCodeReadiness] = []
    for provider in PROVIDERS:
        rows.append(ProviderCodeReadiness(
            provider, "THOROUGHBRED", "TECHNICALLY_AVAILABLE_RIGHTS_PENDING",
            ("Sibling adapter or sanitized validation evidence exists for Australian thoroughbred scope.",),
            ("R-AI-cing Nexus rights, retention, display and model-use approval is absent.", "Real credentials and external connectivity are disabled."),
        ))
        for code in ("HARNESS", "GREYHOUND"):
            rows.append(ProviderCodeReadiness(
                provider, code, "INSUFFICIENT_FEATURE_COVERAGE",
                (f"No provider-specific {code.lower()} historical coverage is established in the audited implementation evidence.",),
                ("Do not infer code support from an Australian or horse-racing endpoint.", "Independent data and rights evidence is required."),
            ))
    code_rows = [
        CodeReadiness(
            "THOROUGHBRED", "TECHNICALLY_AVAILABLE_RIGHTS_PENDING", PROVIDERS,
            ("FormFav catalogue, PuntersEdge results/form, Krok enrichment/results probes and Betfair catalogue/book probes are evidenced.",),
            ("No provider is approved for this application; historical depth and model-use rights remain open.",),
        ),
        CodeReadiness(
            "HARNESS", "INSUFFICIENT_FEATURE_COVERAGE", (),
            ("Only synthetic three-code contract fixtures exist locally.",),
            ("No audited provider establishes sufficient harness form, sectionals, ratings, results and market history.",),
        ),
        CodeReadiness(
            "GREYHOUND", "INSUFFICIENT_FEATURE_COVERAGE", (),
            ("Only synthetic three-code contract fixtures exist locally.",),
            ("No audited provider establishes sufficient greyhound form, split times, box/interference, results and market history.",),
        ),
    ]
    return {
        "report_version": "provider-readiness-v1",
        "external_connectivity": "DISABLED",
        "provider_code_verdicts": [row.to_dict() for row in rows],
        "code_verdicts": [row.to_dict() for row in code_rows],
        "available_and_approved": [],
    }
