"""Evidence-strength, coverage and out-of-distribution diagnostics."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from collections.abc import Mapping, Sequence
from typing import Literal


EvidenceStrength = Literal["HIGH", "MEDIUM", "LOW", "INSUFFICIENT"]


@dataclass(frozen=True)
class DiagnosticConfig:
    minimum_support: int = 2
    maximum_disagreement: float = 0.20
    maximum_ood_score: float = 0.50
    abstain_on_missingness: bool = True
    abstain_on_disagreement: bool = True
    abstain_on_ood: bool = True


@dataclass(frozen=True)
class DiagnosticResult:
    probabilities: dict[str, float]
    evidence_strength: EvidenceStrength
    support_count: int
    coverage: float
    missingness: tuple[str, ...]
    disagreement: float | None
    ood_score: float | None
    ood_warning: bool
    abstain: bool
    abstention_reasons: tuple[str, ...]
    thresholds: dict[str, float | int | bool]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["missingness"] = list(self.missingness)
        payload["abstention_reasons"] = list(self.abstention_reasons)
        return payload


def _validate_probability_map(values: Mapping[str, float]) -> None:
    for entry_id, value in values.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value < 0:
            raise ValueError(f"invalid probability for {entry_id}")


def _disagreement(reference: Mapping[str, float], challenger: Mapping[str, float] | None) -> float | None:
    if challenger is None:
        return None
    if set(reference) != set(challenger):
        raise ValueError("disagreement models must have identical field membership")
    _validate_probability_map(challenger)
    return max((abs(reference[key] - challenger[key]) for key in reference), default=0.0)


def diagnose_forecast(
    probabilities: Mapping[str, float],
    *,
    support_count: int,
    missingness: Sequence[str] = (),
    comparison_probabilities: Mapping[str, float] | None = None,
    ood_score: float | None = None,
    config: DiagnosticConfig = DiagnosticConfig(),
) -> DiagnosticResult:
    """Return evidence diagnostics without changing the probability map."""

    _validate_probability_map(probabilities)
    if support_count < 0 or config.minimum_support <= 0:
        raise ValueError("support counts and minimum_support must be positive")
    if not 0 <= config.maximum_disagreement or not 0 <= config.maximum_ood_score:
        raise ValueError("diagnostic thresholds must be non-negative")
    if ood_score is not None and (not math.isfinite(ood_score) or ood_score < 0):
        raise ValueError("ood_score must be finite and non-negative")
    disagreement = _disagreement(probabilities, comparison_probabilities)
    ood_warning = ood_score is not None and ood_score > config.maximum_ood_score
    reasons: list[str] = []
    if support_count < config.minimum_support:
        reasons.append("INSUFFICIENT_SUPPORT")
    if missingness and config.abstain_on_missingness:
        reasons.append("MISSING_FEATURES")
    if disagreement is not None and disagreement > config.maximum_disagreement and config.abstain_on_disagreement:
        reasons.append("MODEL_DISAGREEMENT")
    if ood_warning and config.abstain_on_ood:
        reasons.append("OUT_OF_DISTRIBUTION")
    if support_count < config.minimum_support:
        strength: EvidenceStrength = "INSUFFICIENT"
    elif reasons:
        strength = "LOW"
    elif missingness or (disagreement is not None and disagreement > config.maximum_disagreement) or ood_warning:
        strength = "MEDIUM"
    else:
        strength = "HIGH"
    coverage = min(1.0, support_count / config.minimum_support)
    return DiagnosticResult(
        probabilities=dict(probabilities), evidence_strength=strength, support_count=support_count,
        coverage=coverage, missingness=tuple(missingness), disagreement=disagreement,
        ood_score=ood_score, ood_warning=ood_warning, abstain=bool(reasons),
        abstention_reasons=tuple(reasons), thresholds={
            "minimum_support": config.minimum_support, "maximum_disagreement": config.maximum_disagreement,
            "maximum_ood_score": config.maximum_ood_score, "abstain_on_missingness": config.abstain_on_missingness,
            "abstain_on_disagreement": config.abstain_on_disagreement, "abstain_on_ood": config.abstain_on_ood,
        },
    )

