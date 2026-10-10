from decimal import Decimal

import pytest

from app.assistant_eval import (
    AssistantPolicy,
    BudgetConfig,
    BudgetLedger,
    DEFAULT_CASES,
    evaluate_cases,
    reference_responder,
)


def test_curated_offline_suite_covers_all_required_case_classes() -> None:
    report = evaluate_cases(DEFAULT_CASES, reference_responder)
    assert report.offline is True
    assert report.total == report.passed == 4
    assert report.failed == 0
    assert {result.category for result in report.results} == {"POSITIVE", "NEGATIVE", "CONTRADICTION", "INJECTION"}


def test_budget_kill_switch_rejects_request_before_usage_is_recorded() -> None:
    ledger = BudgetLedger(BudgetConfig(max_requests=1, max_input_tokens=10, max_output_tokens=10, max_spend_usd=Decimal("0.10")))
    assert ledger.reserve(input_tokens=5, output_tokens=5, spend_usd=Decimal("0.05")) == "ALLOWED"
    assert ledger.reserve(input_tokens=1, output_tokens=1, spend_usd=Decimal("0.01")) == "BUDGET_EXCEEDED"
    assert ledger.requests == 1
    assert ledger.input_tokens == 5
    assert ledger.spend_usd == Decimal("0.05")


def test_budget_rejects_negative_usage_and_invalid_limits() -> None:
    with pytest.raises(ValueError, match="positive"):
        BudgetConfig(max_requests=0)
    ledger = BudgetLedger(BudgetConfig())
    with pytest.raises(ValueError, match="negative"):
        ledger.reserve(input_tokens=-1, output_tokens=0, spend_usd=Decimal("0"))


def test_assistant_is_disabled_until_feature_rights_and_provider_policy_are_approved() -> None:
    assert AssistantPolicy().status() == "FEATURE_DISABLED"
    assert AssistantPolicy(feature_enabled=True, rights_approved=True, provider_policy_approved=False).status() == "FEATURE_DISABLED"
    assert AssistantPolicy(feature_enabled=True, rights_approved=True, provider_policy_approved=True).status() == "ALLOWED"
