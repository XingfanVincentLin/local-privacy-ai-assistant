from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class SensorEvent:
    entity_id: str
    friendly_name: str
    state: str
    unit: str
    domain: str
    last_changed: datetime
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TextChunk:
    id: str
    text: str
    metadata: dict[str, str | int | float | bool]

