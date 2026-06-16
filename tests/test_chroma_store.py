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


def test_chroma_store_boosts_exact_room_and_sensor_terms(tmp_path) -> None:
    store = ChromaStore(
        persist_dir=tmp_path / "chroma",
        collection_name="test_collection",
        embedder=HashingEmbedder(),
    )
    chunks = [
        TextChunk(
            id="chunk-bedroom",
            text=(
                "At 10:00, Bedroom T&H Sensor Temperature "
                "(sensor.bedroom_t_h_sensor_temperature) measured 28.0 C."
            ),
            metadata={
                "entity_id": "sensor.bedroom_t_h_sensor_temperature",
                "friendly_name": "Bedroom T&H Sensor Temperature",
            },
        ),
        TextChunk(
            id="chunk-tv",
            text="At 10:00, TV Power Total energy measured 2.5 kWh.",
            metadata={
                "entity_id": "sensor.tv_power_total_energy",
                "friendly_name": "TV Power Total energy",
            },
        ),
    ]

    store.upsert_chunks(chunks)
    results = store.search("bedroom temperature", k=1)

    assert results[0]["metadata"]["entity_id"] == "sensor.bedroom_t_h_sensor_temperature"


def test_chroma_store_keeps_multi_topic_results_diverse(tmp_path) -> None:
    store = ChromaStore(
        persist_dir=tmp_path / "chroma",
        collection_name="test_collection",
        embedder=HashingEmbedder(),
    )
    chunks = [
        TextChunk(
            id=f"chunk-tv-{index}",
            text=f"At 10:0{index}, TV Power Total energy measured 2.{index} kWh.",
            metadata={
                "entity_id": "sensor.tv_power_total_energy",
                "friendly_name": "TV Power Total energy",
            },
        )
        for index in range(4)
    ]
    chunks.append(
        TextChunk(
            id="chunk-bedroom",
            text=(
                "At 10:00, Bedroom T&H Sensor Temperature "
                "(sensor.bedroom_t_h_sensor_temperature) measured 28.0 C."
            ),
            metadata={
                "entity_id": "sensor.bedroom_t_h_sensor_temperature",
                "friendly_name": "Bedroom T&H Sensor Temperature",
            },
        )
    )

    store.upsert_chunks(chunks)
    results = store.search("bedroom temperature and TV power energy", k=3)
    result_entities = {result["metadata"]["entity_id"] for result in results}

    assert "sensor.tv_power_total_energy" in result_entities
    assert "sensor.bedroom_t_h_sensor_temperature" in result_entities


def test_chroma_store_prefers_recent_chunks_for_latest_questions(tmp_path) -> None:
    store = ChromaStore(
        persist_dir=tmp_path / "chroma",
        collection_name="test_collection",
        embedder=HashingEmbedder(),
    )
    chunks = [
        TextChunk(
            id="chunk-tv-old",
            text="At 09:00, TV Power Total energy measured 2.5 kWh.",
            metadata={
                "entity_id": "sensor.tv_power_total_energy",
                "friendly_name": "TV Power Total energy",
                "end_time": "2026-06-16T09:00:00+00:00",
            },
        ),
        TextChunk(
            id="chunk-tv-new",
            text="At 17:00, TV Power Total energy measured 0.008 kWh.",
            metadata={
                "entity_id": "sensor.tv_power_total_energy",
                "friendly_name": "TV Power Total energy",
                "end_time": "2026-06-16T17:00:00+00:00",
            },
        ),
    ]

    store.upsert_chunks(chunks)
    results = store.search("latest TV power energy", k=1)

    assert results[0]["id"] == "chunk-tv-new"


def test_chroma_store_treats_warmer_questions_as_temperature_questions(tmp_path) -> None:
    store = ChromaStore(
        persist_dir=tmp_path / "chroma",
        collection_name="test_collection",
        embedder=HashingEmbedder(),
    )
    chunks = [
        TextChunk(
            id="chunk-bedroom-temp",
            text="At 17:00, Bedroom Temperature measured 28.0 C.",
            metadata={
                "entity_id": "sensor.bedroom_temperature",
                "friendly_name": "Bedroom Temperature",
                "end_time": "2026-06-16T17:00:00+00:00",
            },
        ),
        TextChunk(
            id="chunk-bathroom-temp",
            text="At 17:00, Bathroom Temperature measured 24.0 C.",
            metadata={
                "entity_id": "sensor.bathroom_temperature",
                "friendly_name": "Bathroom Temperature",
                "end_time": "2026-06-16T17:00:00+00:00",
            },
        ),
        TextChunk(
            id="chunk-bathroom-motion",
            text="At 17:00, Bathroom Motion Sensor was inactive.",
            metadata={
                "entity_id": "binary_sensor.bathroom_motion",
                "friendly_name": "Bathroom Motion Sensor",
                "end_time": "2026-06-16T17:00:00+00:00",
            },
        ),
    ]

    store.upsert_chunks(chunks)
    results = store.search("Which is warmer, the bedroom or bathroom?", k=2)
    result_entities = {result["metadata"]["entity_id"] for result in results}

    assert result_entities == {"sensor.bedroom_temperature", "sensor.bathroom_temperature"}


def test_chroma_store_ignores_state_words_when_latest_state_is_requested(tmp_path) -> None:
    store = ChromaStore(
        persist_dir=tmp_path / "chroma",
        collection_name="test_collection",
        embedder=HashingEmbedder(),
    )
    chunks = [
        TextChunk(
            id="chunk-motion-old",
            text=(
                "At 10:00, Bathroom Motion Sensor was active or detected motion. "
                "At 10:01, it was inactive."
            ),
            metadata={
                "entity_id": "binary_sensor.bathroom_motion",
                "friendly_name": "Bathroom Motion Sensor",
                "end_time": "2026-06-16T10:01:00+00:00",
            },
        ),
        TextChunk(
            id="chunk-motion-new",
            text="At 17:00, Bathroom Motion Sensor was inactive.",
            metadata={
                "entity_id": "binary_sensor.bathroom_motion",
                "friendly_name": "Bathroom Motion Sensor",
                "end_time": "2026-06-16T17:00:00+00:00",
            },
        ),
    ]

    store.upsert_chunks(chunks)
    results = store.search("Was the bathroom motion sensor active or inactive latest?", k=1)

    assert results[0]["id"] == "chunk-motion-new"
