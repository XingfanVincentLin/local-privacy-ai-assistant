from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    ha_base_url: str
    ha_token: str
    ollama_host: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:7b"
    chroma_dir: Path = Path("data/chroma")
    chroma_collection: str = "home_assistant_history"
    entity_ids: tuple[str, ...] = ()

    @classmethod
    def from_env(cls, env_file: str | Path | None = ".env") -> "Settings":
        if env_file:
            load_dotenv(env_file)

        entity_ids = tuple(
            item.strip()
            for item in os.getenv("HA_ENTITY_IDS", "").split(",")
            if item.strip()
        )

        return cls(
            ha_base_url=os.getenv("HA_BASE_URL", "").rstrip("/"),
            ha_token=os.getenv("HA_TOKEN", ""),
            ollama_host=os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/"),
            ollama_model=os.getenv("OLLAMA_MODEL", "qwen2.5:7b"),
            chroma_dir=Path(os.getenv("CHROMA_DIR", "data/chroma")),
            chroma_collection=os.getenv("CHROMA_COLLECTION", "home_assistant_history"),
            entity_ids=entity_ids,
        )

    def validate_for_ingestion(self) -> None:
        missing = []
        if not self.ha_base_url:
            missing.append("HA_BASE_URL")
        if not self.ha_token:
            missing.append("HA_TOKEN")
        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"Missing required Home Assistant setting(s): {joined}")

