from __future__ import annotations

import hashlib
from collections import defaultdict

from .models import SensorEvent, TextChunk
from .normalizer import event_to_sentence


def chunk_events_by_hour(events: list[SensorEvent], max_sentences: int = 18) -> list[TextChunk]:
    grouped: dict[tuple[str, str], list[SensorEvent]] = defaultdict(list)
    for event in events:
        hour_key = event.last_changed.strftime("%Y-%m-%d %H:00")
        grouped[(event.entity_id, hour_key)].append(event)

    chunks: list[TextChunk] = []
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

