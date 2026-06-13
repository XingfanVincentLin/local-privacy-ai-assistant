from __future__ import annotations

from functools import lru_cache

from local_privacy_ai.config import Settings
from local_privacy_ai.llm.ollama_client import OllamaClient
from local_privacy_ai.rag.orchestrator import RAGOrchestrator
from local_privacy_ai.storage.chroma_store import ChromaStore
from local_privacy_ai.storage.embeddings import SentenceTransformerEmbedder


def build_orchestrator(settings: Settings | None = None) -> RAGOrchestrator:
    resolved = settings or Settings.from_env()
    embedder = SentenceTransformerEmbedder()
    store = ChromaStore(
        persist_dir=resolved.chroma_dir,
        collection_name=resolved.chroma_collection,
        embedder=embedder,
    )
    llm = OllamaClient(host=resolved.ollama_host, model=resolved.ollama_model)
    return RAGOrchestrator(store=store, llm=llm)


@lru_cache(maxsize=1)
def build_default_orchestrator() -> RAGOrchestrator:
    return build_orchestrator(Settings.from_env())
