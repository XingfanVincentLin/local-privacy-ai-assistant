from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from local_privacy_ai.ingestion.models import TextChunk

from .embeddings import EmbeddingModel

STOPWORDS = {
    "about",
    "active",
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "available",
    "can",
    "current",
    "did",
    "does",
    "for",
    "from",
    "have",
    "how",
    "in",
    "inactive",
    "is",
    "it",
    "into",
    "know",
    "latest",
    "me",
    "now",
    "of",
    "on",
    "or",
    "reading",
    "readings",
    "tell",
    "the",
    "this",
    "state",
    "states",
    "to",
    "what",
    "when",
    "where",
    "was",
    "were",
    "which",
    "with",
    "you",
}

RECENCY_TERMS = {"current", "currently", "latest", "now", "recent", "recently"}
TEMPERATURE_INTENT_TERMS = {
    "cold",
    "colder",
    "cool",
    "cooler",
    "hot",
    "hotter",
    "warm",
    "warmer",
}


def _raw_tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", value.lower())
        if len(token) > 1 and token not in STOPWORDS
    }


def _has_recency_intent(query: str) -> bool:
    return bool(_raw_tokens(query) & RECENCY_TERMS)


def _query_terms(query: str) -> set[str]:
    raw_terms = _raw_tokens(query)
    query_terms = _tokens(query)
    if raw_terms & TEMPERATURE_INTENT_TERMS:
        query_terms.add("temperature")
    return query_terms


def _searchable_text(document: str, metadata: dict) -> str:
    metadata_text = " ".join(str(value) for value in metadata.values())
    return f"{document} {metadata_text}"


def _lexical_score(query_terms: set[str], document: str, metadata: dict) -> int:
    if not query_terms:
        return 0
    source_terms = _tokens(_searchable_text(document, metadata))
    return len(query_terms & source_terms)


def _recency_score(metadata: dict) -> float:
    raw_timestamp = metadata.get("end_time") or metadata.get("start_time")
    if not raw_timestamp:
        return 0.0
    try:
        return datetime.fromisoformat(str(raw_timestamp)).timestamp()
    except ValueError:
        return 0.0


def _diverse_top_k(sources: list[dict], k: int) -> list[dict]:
    max_per_entity = max(2, min(4, (k + 1) // 2))
    selected: list[dict] = []
    skipped: list[dict] = []
    entity_counts: dict[str, int] = {}

    for source in sources:
        entity_id = str(source["metadata"].get("entity_id", source["id"]))
        if entity_counts.get(entity_id, 0) < max_per_entity:
            selected.append(source)
            entity_counts[entity_id] = entity_counts.get(entity_id, 0) + 1
        else:
            skipped.append(source)
        if len(selected) == k:
            return selected

    return (selected + skipped)[:k]


class ChromaStore:
    def __init__(
        self,
        persist_dir: Path,
        collection_name: str,
        embedder: EmbeddingModel,
    ) -> None:
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        self.embedder = embedder
        persist_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def upsert_chunks(self, chunks: list[TextChunk]) -> int:
        if not chunks:
            return 0
        embeddings = self.embedder.embed([chunk.text for chunk in chunks])
        self.collection.upsert(
            ids=[chunk.id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            metadatas=[chunk.metadata for chunk in chunks],
            embeddings=embeddings,
        )
        return len(chunks)

    def search(self, query: str, k: int = 5) -> list[dict]:
        count = self.collection.count()
        if count == 0:
            return []

        query_terms = _query_terms(query)
        has_recency_intent = _has_recency_intent(query)
        vector_k = min(count, max(k, k * 6))
        embedding = self.embedder.embed([query])[0]
        result = self.collection.query(
            query_embeddings=[embedding],
            n_results=vector_k,
            include=["documents", "metadatas", "distances"],
        )
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        ids = result.get("ids", [[]])[0]
        candidates: dict[str, dict] = {}
        for chunk_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
            metadata = metadata or {}
            candidates[chunk_id] = {
                "id": chunk_id,
                "text": document,
                "metadata": metadata,
                "distance": distance,
                "lexical_score": _lexical_score(query_terms, document, metadata),
                "recency_score": _recency_score(metadata),
            }

        lexical_result = self.collection.get(include=["documents", "metadatas"])
        for chunk_id, document, metadata in zip(
            lexical_result.get("ids", []),
            lexical_result.get("documents", []),
            lexical_result.get("metadatas", []),
        ):
            metadata = metadata or {}
            lexical_score = _lexical_score(query_terms, document, metadata)
            if lexical_score <= 0:
                continue
            existing = candidates.get(chunk_id)
            if existing:
                existing["lexical_score"] = max(existing["lexical_score"], lexical_score)
                continue
            candidates[chunk_id] = {
                "id": chunk_id,
                "text": document,
                "metadata": metadata,
                "distance": None,
                "lexical_score": lexical_score,
                "recency_score": _recency_score(metadata),
            }

        def sort_key(source: dict) -> tuple[float, ...]:
            distance = source["distance"]
            vector_score = 0.0 if distance is None else 1.0 / (1.0 + float(distance))
            lexical_score = float(source["lexical_score"]) * 2.0
            if has_recency_intent:
                return (lexical_score, float(source["recency_score"]), vector_score)
            return (lexical_score + vector_score, vector_score)

        ranked_sources = sorted(candidates.values(), key=sort_key, reverse=True)
        return _diverse_top_k(ranked_sources, k)
