from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from local_privacy_ai.config import Settings
from local_privacy_ai.ingestion.chunker import chunk_events_by_hour
from local_privacy_ai.ingestion.ha_client import HomeAssistantClient
from local_privacy_ai.ingestion.normalizer import normalize_history_payload
from local_privacy_ai.storage.chroma_store import ChromaStore
from local_privacy_ai.storage.embeddings import SentenceTransformerEmbedder


async def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Home Assistant history into ChromaDB.")
    parser.add_argument("--hours", type=int, default=24, help="Number of history hours to ingest.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear the Chroma collection before ingesting the selected history window.",
    )
    args = parser.parse_args()

    settings = Settings.from_env()
    settings.validate_for_ingestion()

    client = HomeAssistantClient(settings.ha_base_url, settings.ha_token)
    payload = await client.get_history(hours=args.hours, entity_ids=settings.entity_ids)
    events = normalize_history_payload(payload)
    chunks = chunk_events_by_hour(events)

    store = ChromaStore(
        persist_dir=settings.chroma_dir,
        collection_name=settings.chroma_collection,
        embedder=SentenceTransformerEmbedder(),
    )
    if args.reset:
        removed = store.clear()
        print(f"Cleared {removed} existing chunks from the collection.")
    inserted = store.upsert_chunks(chunks)
    print(f"Ingested {len(events)} events into {inserted} chunks.")


if __name__ == "__main__":
    asyncio.run(main())
