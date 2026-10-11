import pytest

from app.database_safety import validate_disposable_database_url


def test_disposable_database_target_requires_explicit_loopback_confirmation() -> None:
    target = validate_disposable_database_url(
        "postgresql+psycopg://user:secret@127.0.0.1:5432/racing_intelligence_dev",
        confirmation="1",
    )
    assert target.host == "127.0.0.1"
    assert target.database == "racing_intelligence_dev"


@pytest.mark.parametrize(
    "url,confirmation,error",
    [
        ("postgresql+psycopg://user:secret@db.example/racing_intelligence_dev", "1", "loopback"),
        ("postgresql+psycopg://user:secret@127.0.0.1/racing_intelligence", "1", "database name"),
        ("postgresql+psycopg://user:secret@127.0.0.1/racing_intelligence_dev", None, "RACING_INTELLIGENCE_DB_DISPOSABLE"),
        ("sqlite:///racing_intelligence_dev.db", "1", "PostgreSQL"),
    ],
)
def test_non_disposable_database_targets_fail_closed(url: str, confirmation: str | None, error: str) -> None:
    with pytest.raises(ValueError, match=error):
        validate_disposable_database_url(url, confirmation=confirmation)
