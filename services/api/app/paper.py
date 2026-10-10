"""Paper-only value and settlement scenarios; no external execution path."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


FillStatus = Literal["FILLED", "PARTIAL", "UNFILLED", "SCRATCHED"]
SettlementOutcome = Literal["WIN", "LOSS", "VOID", "DEAD_HEAT", "SCRATCHED"]


class PaperSimulationError(ValueError):
    """Raised when a paper scenario violates its explicit assumptions."""


@dataclass(frozen=True)
class PaperAssumptions:
    fee_rate: float = 0.0
    commission_rate: float = 0.0
    fill_ratio: float = 1.0
    max_exposure: float = 1000.0

    def __post_init__(self) -> None:
        for name, value in (("fee_rate", self.fee_rate), ("commission_rate", self.commission_rate), ("fill_ratio", self.fill_ratio)):
            if not 0 <= value <= 1:
                raise PaperSimulationError(f"{name} must be between 0 and 1")
        if self.max_exposure <= 0:
            raise PaperSimulationError("max_exposure must be positive")


@dataclass(frozen=True)
class PaperPosition:
    position_id: str
    selection_id: str
    requested_stake: float
    matched_stake: float
    price: float
    liquidity: float | None
    fill_status: FillStatus
    fee: float
    exposure: float


@dataclass(frozen=True)
class PaperSettlement:
    position_id: str
    outcome: SettlementOutcome
    matched_stake: float
    gross_profit: float
    commission: float
    fee: float
    removal_factor: float
    dead_heat_places: int
    net_result: float
    guaranteed: bool = False


class PaperLedger:
    """Append-only paper scenario ledger with explicit exposure assumptions."""

    def __init__(self, assumptions: PaperAssumptions | None = None) -> None:
        self.assumptions = assumptions or PaperAssumptions()
        self._positions: dict[str, PaperPosition] = {}
        self._settlements: dict[str, PaperSettlement] = {}

    def record_position(
        self,
        position_id: str,
        selection_id: str,
        requested_stake: float,
        price: float,
        liquidity: float | None,
        *,
        scratched: bool = False,
    ) -> PaperPosition:
        if position_id in self._positions:
            raise PaperSimulationError("paper positions are append-only")
        if not position_id.strip() or not selection_id.strip():
            raise PaperSimulationError("position and selection identifiers are required")
        if requested_stake <= 0 or price < 1:
            raise PaperSimulationError("stake must be positive and decimal price must be at least 1")
        if liquidity is not None and liquidity < 0:
            raise PaperSimulationError("liquidity cannot be negative")
        if scratched:
            matched = 0.0
            fill_status: FillStatus = "SCRATCHED"
        elif liquidity is None or liquidity == 0:
            matched = 0.0
            fill_status = "UNFILLED"
        else:
            matched = min(requested_stake, liquidity) * self.assumptions.fill_ratio
            fill_status = "FILLED" if matched == requested_stake else "PARTIAL"
        fee = matched * self.assumptions.fee_rate
        exposure = matched + fee
        if self.current_exposure() + exposure > self.assumptions.max_exposure:
            raise PaperSimulationError("paper exposure assumption would be exceeded")
        position = PaperPosition(position_id, selection_id, requested_stake, _round(matched), price, liquidity, fill_status, _round(fee), _round(exposure))
        self._positions[position_id] = position
        return position

    def settle(
        self,
        position_id: str,
        outcome: SettlementOutcome,
        *,
        removal_factor: float = 0.0,
        dead_heat_places: int = 1,
    ) -> PaperSettlement:
        if position_id in self._settlements:
            raise PaperSimulationError("paper settlements are append-only")
        if position_id not in self._positions:
            raise PaperSimulationError("paper position was not found")
        if not 0 <= removal_factor <= 1:
            raise PaperSimulationError("removal_factor must be between 0 and 1")
        if dead_heat_places < 1:
            raise PaperSimulationError("dead_heat_places must be positive")
        position = self._positions[position_id]
        if outcome in {"VOID", "SCRATCHED"}:
            gross_profit = 0.0
            commission = 0.0
        elif outcome == "WIN" or outcome == "DEAD_HEAT":
            gross_profit = position.matched_stake * (position.price - 1) * (1 - removal_factor) / (dead_heat_places if outcome == "DEAD_HEAT" else 1)
            commission = gross_profit * self.assumptions.commission_rate
        else:
            gross_profit = -position.matched_stake
            commission = 0.0
        net_result = gross_profit - commission - position.fee
        settlement = PaperSettlement(
            position_id, outcome, position.matched_stake, _round(gross_profit), _round(commission), position.fee,
            removal_factor, dead_heat_places, _round(net_result), False,
        )
        self._settlements[position_id] = settlement
        return settlement

    def current_exposure(self) -> float:
        return _round(sum(position.exposure for position in self._positions.values()))

    def snapshot(self) -> dict[str, object]:
        return {
            "assumptions": {
                "fee_rate": self.assumptions.fee_rate,
                "commission_rate": self.assumptions.commission_rate,
                "fill_ratio": self.assumptions.fill_ratio,
                "max_exposure": self.assumptions.max_exposure,
            },
            "positions": [position.__dict__ for position in self._positions.values()],
            "settlements": [settlement.__dict__ for settlement in self._settlements.values()],
            "guaranteed_returns": False,
            "paper_only": True,
        }


def _round(value: float) -> float:
    return round(value, 8)
