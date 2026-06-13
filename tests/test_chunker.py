from __future__ import annotations

from datetime import datetime, timezone

from local_privacy_ai.ingestion.chunker import chunk_events_by_hour
from local_privacy_ai.ingestion.models import SensorEvent


def test_chunk_events_by_hour_groups_by_entity_and_hour() -> None:
    events = [
        SensorEvent(
            entity_id="sensor.bedroom_temperature",
            friendly_name="Bedroom Temperature",
            state="21.5",
            unit="C",
            domain="sensor",
            last_changed=datetime(2026, 6, 13, 10, 5, tzinfo=timezone.utc),
            attributes={"device_class": "temperature"},
        ),
        SensorEvent(
            entity_id="sensor.bedroom_temperature",
            friendly_name="Bedroom Temperature",
            state="22.0",
            unit="C",
            domain="sensor",
            last_changed=datetime(2026, 6, 13, 10, 45, tzinfo=timezone.utc),
            attributes={"device_class": "temperature"},
        ),
    ]

    chunks = chunk_events_by_hour(events)

    assert len(chunks) == 1
    assert "Bedroom Temperature" in chunks[0].text
    assert chunks[0].metadata["event_count"] == 2

