from pathlib import Path


def test_api_source_contains_no_live_execution_path() -> None:
    root = Path(__file__).resolve().parents[1] / "app"
    source = "\n".join(path.read_text(encoding="utf-8").lower() for path in root.glob("*.py"))
    for forbidden in ("place_bet", "submit_bet", "bookmaker", "auto_bet", "/orders"):
        assert forbidden not in source
