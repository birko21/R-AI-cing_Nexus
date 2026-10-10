from __future__ import annotations

import pytest

from app.paper import PaperAssumptions, PaperLedger, PaperSimulationError


def test_paper_ledger_models_fees_commission_and_full_fill() -> None:
    ledger = PaperLedger(PaperAssumptions(fee_rate=0.02, commission_rate=0.1, fill_ratio=1, max_exposure=100))
    position = ledger.record_position("p1", "selection-1", 10, 3, 100)
    settlement = ledger.settle("p1", "WIN")

    assert position.fill_status == "FILLED"
    assert position.matched_stake == 10
    assert settlement.gross_profit == 20
    assert settlement.commission == 2
    assert settlement.fee == 0.2
    assert settlement.net_result == 17.8
    assert settlement.guaranteed is False


def test_liquidity_and_fill_ratio_produce_partial_fill_and_exposure() -> None:
    ledger = PaperLedger(PaperAssumptions(fill_ratio=0.5, max_exposure=100))
    position = ledger.record_position("p1", "selection-1", 10, 2, 6)

    assert position.fill_status == "PARTIAL"
    assert position.matched_stake == 3
    assert ledger.current_exposure() == 3


def test_scratchings_and_voids_have_no_profit_and_no_fabricated_fill() -> None:
    ledger = PaperLedger()
    scratched = ledger.record_position("p1", "selection-1", 10, 3, 100, scratched=True)
    ledger.record_position("p2", "selection-2", 10, 3, 100)

    scratched_settlement = ledger.settle("p1", "SCRATCHED")
    void_settlement = ledger.settle("p2", "VOID")

    assert scratched.fill_status == "SCRATCHED" and scratched.matched_stake == 0
    assert scratched_settlement.net_result == 0
    assert void_settlement.net_result == -0.0


def test_dead_heat_and_removal_factor_are_explicit_assumptions() -> None:
    ledger = PaperLedger(PaperAssumptions(commission_rate=0.1))
    ledger.record_position("p1", "selection-1", 10, 5, 100)

    settlement = ledger.settle("p1", "DEAD_HEAT", removal_factor=0.2, dead_heat_places=2)

    assert settlement.gross_profit == 16
    assert settlement.commission == 1.6
    assert settlement.net_result == 14.4
    assert settlement.dead_heat_places == 2


def test_loss_and_unfilled_liquidity_are_recorded_without_return_claims() -> None:
    ledger = PaperLedger()
    position = ledger.record_position("p1", "selection-1", 10, 2, None)
    settlement = ledger.settle("p1", "LOSS")

    assert position.fill_status == "UNFILLED"
    assert settlement.net_result == 0
    assert ledger.snapshot()["guaranteed_returns"] is False
    assert ledger.snapshot()["paper_only"] is True


def test_exposure_limit_and_append_only_guards_are_enforced() -> None:
    ledger = PaperLedger(PaperAssumptions(max_exposure=5))
    ledger.record_position("p1", "selection-1", 5, 2, 100)
    with pytest.raises(PaperSimulationError, match="exposure"):
        ledger.record_position("p2", "selection-2", 1, 2, 100)
    with pytest.raises(PaperSimulationError, match="append-only"):
        ledger.record_position("p1", "selection-1", 1, 2, 100)
    ledger.settle("p1", "WIN")
    with pytest.raises(PaperSimulationError, match="append-only"):
        ledger.settle("p1", "WIN")
