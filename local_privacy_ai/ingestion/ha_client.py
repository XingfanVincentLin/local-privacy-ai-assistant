from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx


class HomeAssistantClient:
    """Small wrapper around the Home Assistant REST history API."""

    def __init__(
        self,
        base_url: str,
        token: str,
        timeout: float = 30.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.transport = transport
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def get_history(
        self,
        hours: int = 24,
        entity_ids: tuple[str, ...] = (),
        end_time: datetime | None = None,
    ) -> list[list[dict[str, Any]]]:
        end = end_time or datetime.now(timezone.utc)
        start = end - timedelta(hours=hours)
        url = f"{self.base_url}/api/history/period/{start.isoformat()}"
        params: dict[str, str] = {"end_time": end.isoformat()}
        if entity_ids:
            params["filter_entity_id"] = ",".join(entity_ids)

        async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list):
                raise ValueError("Unexpected Home Assistant history response shape")
            return payload

    async def get_states(self) -> list[dict[str, Any]]:
        url = f"{self.base_url}/api/states"
        async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list):
                raise ValueError("Unexpected Home Assistant states response shape")
            return payload
