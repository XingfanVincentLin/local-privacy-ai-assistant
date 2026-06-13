from __future__ import annotations

from pathlib import Path

from local_privacy_ai.ingestion.models import TextChunk

from .embeddings import EmbeddingModel


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
        embedding = self.embedder.embed([query])[0]
        result = self.collection.query(
            query_embeddings=[embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        ids = result.get("ids", [[]])[0]
        sources: list[dict] = []
        for chunk_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
            sources.append(
                {
                    "id": chunk_id,
                    "text": document,
                    "metadata": metadata or {},
                    "distance": distance,
                }
            )
        return sources
