import pytest

from app.runtime_config import load_runtime_config


def test_local_default_remains_explicitly_synthetic() -> None:
    config = load_runtime_config(environ={})
    assert config.data_mode == "SYNTHETIC_ONLY"
    assert config.persistence == "synthetic"
    assert config.live_enabled is False


def test_licensed_mode_requires_postgres_and_scope() -> None:
    with pytest.raises(RuntimeError, match="requires NEXUS_API_PERSISTENCE=postgres"):
        load_runtime_config(environ={"NEXUS_DATA_MODE": "LICENSED"})

    with pytest.raises(RuntimeError, match="requires NEXUS_LIVE_PROVIDER"):
        load_runtime_config(environ={"NEXUS_DATA_MODE": "LICENSED", "NEXUS_API_PERSISTENCE": "postgres"})


def test_licensed_mode_requires_explicit_read_only_scope() -> None:
    config = load_runtime_config(
        environ={
            "NEXUS_DATA_MODE": "LICENSED",
            "NEXUS_API_PERSISTENCE": "postgres",
            "NEXUS_LIVE_PROVIDER": "punters-edge",
            "NEXUS_LIVE_OPERATIONS": "GET_RESULTS",
            "NEXUS_LIVE_CODES": "THOROUGHBRED",
        }
    )
    assert config.live_enabled is True
    assert config.read_only is True

    with pytest.raises(RuntimeError, match="read-only"):
        load_runtime_config(
            environ={
                "NEXUS_DATA_MODE": "LICENSED",
                "NEXUS_API_PERSISTENCE": "postgres",
                "NEXUS_LIVE_PROVIDER": "punters-edge",
                "NEXUS_LIVE_OPERATIONS": "GET_RESULTS",
                "NEXUS_LIVE_CODES": "THOROUGHBRED",
                "NEXUS_LIVE_READ_ONLY": "false",
            }
        )


