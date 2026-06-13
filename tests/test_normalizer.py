from __future__ import annotations

from local_privacy_ai.ingestion.normalizer import event_to_sentence, normalize_history_payload


def test_normalize_history_payload_extracts_sensor_metadata() -> None:
    payload = [
        [
            {
                "entity_id": "sensor.tv_power",
                "state": "42.3",
                "last_changed": "2026-06-13T09:00:00+00:00",
                "attributes": {
                    "friendly_name": "TV Power",
                    "unit_of_measurement": "W",
                    "device_class": "power",
                },
            }
        ]
    ]

    events = normalize_history_payload(payload)

    assert len(events) == 1
    assert events[0].friendly_name == "TV Power"
    assert events[0].unit == "W"
    assert "measured 42.3 W" in event_to_sentence(events[0])

