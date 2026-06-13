from __future__ import annotations

import pytest

from local_privacy_ai.config import Settings


def test_validate_for_ingestion_requires_home_assistant_settings() -> None:
    settings = Settings(ha_base_url="", ha_token="")

    with pytest.raises(ValueError) as exc:
        settings.validate_for_ingestion()

    assert "HA_BASE_URL" in str(exc.value)
    assert "HA_TOKEN" in str(exc.value)


def test_settings_from_env_parses_entity_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HA_BASE_URL", "http://homeassistant.local:8123")
    monkeypatch.setenv("HA_TOKEN", "token")
    monkeypatch.setenv("HA_ENTITY_IDS", "sensor.tv_power, binary_sensor.motion ")

    settings = Settings.from_env(env_file=None)

    assert settings.entity_ids == ("sensor.tv_power", "binary_sensor.motion")

