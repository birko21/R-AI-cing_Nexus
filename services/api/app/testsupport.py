from __future__ import annotations

from datetime import datetime, timezone


NOW = datetime(2026, 1, 15, 10, tzinfo=timezone.utc)


def quote_fixture(quote_id: str, selection_id: str, **overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "quote_id": quote_id,
        "mapping": {
            "mapping_id": f"map-{selection_id}", "code": "THOROUGHBRED", "race_id": "THOROUGHBRED:fixture:race-1",
            "field_revision": "field-r1", "entry_id": f"THOROUGHBRED:fixture:{selection_id}", "market_source": "fixture",
            "market_id": "market-1", "selection_id": selection_id,
        },
        "market_type": "WIN", "price_type": "DECIMAL", "price": 3.5,
        "source_timestamp": NOW, "retrieved_at": NOW, "in_play": False,
        "entitlement_reference": "synthetic-fixture", "source_receipt_id": "receipt-1",
        "data_mode": "SYNTHETIC_ONLY", "rights_state": "SYNTHETIC",
    }
    value.update(overrides)
    return value
