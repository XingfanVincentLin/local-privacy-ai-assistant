from __future__ import annotations

from local_privacy_ai.ingestion.models import TextChunk
from local_privacy_ai.storage.chroma_store import ChromaStore
from local_privacy_ai.storage.embeddings import HashingEmbedder


def test_chroma_store_upserts_and_searches_chunks(tmp_path) -> None:
    store = ChromaStore(
        persist_dir=tmp_path / "chroma",
        collection_name="test_collection",
        embedder=HashingEmbedder(),
    )
    chunks = [
        TextChunk(
            id="chunk-1",
            text="At 10:00, TV Power measured 42 W.",
            metadata={"entity_id": "sensor.tv_power"},
        )
    ]

    inserted = store.upsert_chunks(chunks)
    results = store.search("TV power", k=1)

    assert inserted == 1
    assert len(results) == 1
    assert results[0]["metadata"]["entity_id"] == "sensor.tv_power"

