from __future__ import annotations

from datetime import datetime
from typing import Any

from .models import SensorEvent


def parse_home_assistant_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def normalize_history_payload(payload: list[list[dict[str, Any]]]) -> list[SensorEvent]:
    events: list[SensorEvent] = []
    for entity_history in payload:
        for raw in entity_history:
            entity_id = str(raw.get("entity_id", "unknown"))
            attributes = raw.get("attributes") or {}
            domain = entity_id.split(".", 1)[0] if "." in entity_id else "unknown"
            friendly_name = str(attributes.get("friendly_name") or entity_id)
            unit = str(attributes.get("unit_of_measurement") or "")
            timestamp = str(raw.get("last_changed") or raw.get("last_updated"))
            if not timestamp:
                continue
            events.append(
                SensorEvent(
                    entity_id=entity_id,
                    friendly_name=friendly_name,
                    state=str(raw.get("state", "unknown")),
                    unit=unit,
                    domain=domain,
                    last_changed=parse_home_assistant_datetime(timestamp),
                    attributes=attributes,
                )
            )
    return sorted(events, key=lambda event: event.last_changed)


def event_to_sentence(event: SensorEvent) -> str:
    timestamp = event.last_changed.strftime("%Y-%m-%d %H:%M")
    label = event.friendly_name
    state = event.state
    unit = f" {event.unit}" if event.unit else ""

    if event.domain == "binary_sensor":
        if state == "on":
            meaning = "was active or detected motion"
        elif state == "off":
            meaning = "was inactive"
        else:
            meaning = f"reported state {state}"
        return f"At {timestamp}, {label} ({event.entity_id}) {meaning}."

    if event.domain == "sensor":
        device_class = str(event.attributes.get("device_class", "")).lower()
        if device_class in {"temperature", "energy", "power", "illuminance"}:
            return f"At {timestamp}, {label} ({event.entity_id}) measured {state}{unit}."
        return f"At {timestamp}, {label} ({event.entity_id}) reported {state}{unit}."

    if event.domain in {"switch", "light"}:
        return f"At {timestamp}, {label} ({event.entity_id}) was {state}."

    return f"At {timestamp}, {label} ({event.entity_id}) had state {state}{unit}."

