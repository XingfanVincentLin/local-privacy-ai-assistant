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
    hourly_chunks = [chunk for chunk in chunks if chunk.metadata.get("chunk_type") != "entity_summary"]
    summary_chunks = [chunk for chunk in chunks if chunk.metadata.get("chunk_type") == "entity_summary"]

    assert len(hourly_chunks) == 1
    assert len(summary_chunks) == 1
    assert "Bedroom Temperature" in hourly_chunks[0].text
    assert hourly_chunks[0].metadata["event_count"] == 2
    assert "Maximum captured value: 22.0 C" in summary_chunks[0].text


def test_chunk_events_by_hour_adds_motion_summary() -> None:
    events = [
        SensorEvent(
            entity_id="binary_sensor.kitchen_motion",
            friendly_name="Kitchen Motion",
            state="on",
            unit="",
            domain="binary_sensor",
            last_changed=datetime(2026, 6, 13, 10, 5, tzinfo=timezone.utc),
        ),
        SensorEvent(
            entity_id="binary_sensor.kitchen_motion",
            friendly_name="Kitchen Motion",
            state="off",
            unit="",
            domain="binary_sensor",
            last_changed=datetime(2026, 6, 13, 10, 10, tzinfo=timezone.utc),
        ),
    ]

    chunks = chunk_events_by_hour(events)
    summary = next(chunk for chunk in chunks if chunk.metadata.get("chunk_type") == "entity_summary")

    assert "1 active or detected motion readings" in summary.text
    assert "1 inactive readings" in summary.text
    assert "Latest motion state: inactive at 2026-06-13 10:10" in summary.text
