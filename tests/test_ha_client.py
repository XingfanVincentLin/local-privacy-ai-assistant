from __future__ import annotations

import httpx
import pytest

from local_privacy_ai.ingestion.ha_client import HomeAssistantClient


@pytest.mark.anyio
async def test_get_states_returns_home_assistant_states() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/states"
        assert request.headers["authorization"] == "Bearer token"
        return httpx.Response(
            200,
            json=[
                {
                    "entity_id": "sensor.tv_power",
                    "state": "42",
                    "attributes": {"friendly_name": "TV Power"},
                }
            ],
        )

    client = HomeAssistantClient(
        "http://homeassistant.local:8123",
        "token",
        transport=httpx.MockTransport(handler),
    )

    states = await client.get_states()

    assert states[0]["entity_id"] == "sensor.tv_power"


@pytest.mark.anyio
async def test_get_history_sends_entity_filter() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.startswith("/api/history/period/")
        assert request.url.params["filter_entity_id"] == "sensor.tv_power,binary_sensor.motion"
        return httpx.Response(200, json=[[]])

    client = HomeAssistantClient(
        "http://homeassistant.local:8123",
        "token",
        transport=httpx.MockTransport(handler),
    )

    history = await client.get_history(
        hours=1,
        entity_ids=("sensor.tv_power", "binary_sensor.motion"),
    )

    assert history == [[]]
