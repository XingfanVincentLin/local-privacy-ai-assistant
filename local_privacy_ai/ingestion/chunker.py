from __future__ import annotations

import hashlib
from collections import Counter, defaultdict

from .models import SensorEvent, TextChunk
from .normalizer import event_to_sentence


def _format_timestamp(event: SensorEvent) -> str:
    return event.last_changed.strftime("%Y-%m-%d %H:%M")


def _format_value(event: SensorEvent) -> str:
    unit = f" {event.unit}" if event.unit else ""
    return f"{event.state}{unit}"


def _numeric_value(event: SensorEvent) -> float | None:
    try:
        return float(event.state)
    except ValueError:
        return None


def _motion_label(event: SensorEvent) -> str:
    if event.state == "on":
        return "active or detected motion"
    if event.state == "off":
        return "inactive"
    return event.state


def _build_entity_summary(entity_id: str, events: list[SensorEvent]) -> TextChunk:
    ordered = sorted(events, key=lambda event: event.last_changed)
    first = ordered[0]
    latest = ordered[-1]
    lines = [
        (
            f"Summary for {first.friendly_name} ({entity_id}): captured {len(ordered)} "
            f"events from {_format_timestamp(first)} to {_format_timestamp(latest)}."
        ),
        f"First captured state: {_format_value(first)} at {_format_timestamp(first)}.",
        f"Latest captured state: {_format_value(latest)} at {_format_timestamp(latest)}.",
    ]

    numeric_events = [(value, event) for event in ordered if (value := _numeric_value(event)) is not None]
    if numeric_events:
        minimum = min(numeric_events, key=lambda item: item[0])
        maximum = max(numeric_events, key=lambda item: item[0])
        lines.extend(
            [
                (
                    f"Minimum captured value: {_format_value(minimum[1])} "
                    f"at {_format_timestamp(minimum[1])}."
                ),
                (
                    f"Maximum captured value: {_format_value(maximum[1])} "
                    f"at {_format_timestamp(maximum[1])}."
                ),
            ]
        )
        unique_values = {value for value, _event in numeric_events}
        if len(unique_values) == 1:
            lines.append(f"All captured numeric readings stayed at {_format_value(latest)}.")
        else:
            lines.append(
                (
                    f"Captured numeric readings changed from {_format_value(first)} "
                    f"to {_format_value(latest)}."
                )
            )

    if first.domain == "binary_sensor":
        active_events = [event for event in ordered if event.state == "on"]
        inactive_events = [event for event in ordered if event.state == "off"]
        lines.append(
            (
                "Motion/state counts: "
                f"{len(active_events)} active or detected motion readings and "
                f"{len(inactive_events)} inactive readings."
            )
        )
        if active_events:
            lines.append(
                (
                    f"First active event: {_motion_label(active_events[0])} "
                    f"at {_format_timestamp(active_events[0])}."
                )
            )
            lines.append(
                (
                    f"Latest active event: {_motion_label(active_events[-1])} "
                    f"at {_format_timestamp(active_events[-1])}."
                )
            )
        lines.append(
            f"Latest motion state: {_motion_label(latest)} at {_format_timestamp(latest)}."
        )

    if first.domain in {"light", "switch"}:
        state_counts = Counter(event.state for event in ordered)
        count_text = ", ".join(f"{state}={count}" for state, count in sorted(state_counts.items()))
        lines.append(f"State counts: {count_text}.")
        lines.append(f"Latest device state: {latest.state} at {_format_timestamp(latest)}.")

    digest = hashlib.sha1(
        f"{entity_id}:summary:{first.last_changed.isoformat()}:{latest.last_changed.isoformat()}".encode()
    ).hexdigest()[:12]
    return TextChunk(
        id=f"{entity_id}:summary:{digest}",
        text="\n".join(lines),
        metadata={
            "entity_id": entity_id,
            "friendly_name": first.friendly_name,
            "domain": first.domain,
            "chunk_type": "entity_summary",
            "start_time": first.last_changed.isoformat(),
            "end_time": latest.last_changed.isoformat(),
            "event_count": len(ordered),
        },
    )


def chunk_events_by_hour(events: list[SensorEvent], max_sentences: int = 18) -> list[TextChunk]:
    grouped: dict[tuple[str, str], list[SensorEvent]] = defaultdict(list)
    by_entity: dict[str, list[SensorEvent]] = defaultdict(list)
    for event in events:
        hour_key = event.last_changed.strftime("%Y-%m-%d %H:00")
        grouped[(event.entity_id, hour_key)].append(event)
        by_entity[event.entity_id].append(event)

    chunks: list[TextChunk] = []
    for entity_id, entity_events in sorted(by_entity.items()):
        chunks.append(_build_entity_summary(entity_id, entity_events))

    for (entity_id, hour_key), group in sorted(grouped.items()):
        for index in range(0, len(group), max_sentences):
            batch = group[index : index + max_sentences]
            text = "\n".join(event_to_sentence(event) for event in batch)
            first = batch[0]
            last = batch[-1]
            digest = hashlib.sha1(
                f"{entity_id}:{hour_key}:{index}:{first.last_changed.isoformat()}".encode()
            ).hexdigest()[:12]
            chunks.append(
                TextChunk(
                    id=f"{entity_id}:{hour_key}:{index}:{digest}",
                    text=text,
                    metadata={
                        "entity_id": entity_id,
                        "friendly_name": first.friendly_name,
                        "domain": first.domain,
                        "start_time": first.last_changed.isoformat(),
                        "end_time": last.last_changed.isoformat(),
                        "event_count": len(batch),
                    },
                )
            )
    return chunks
