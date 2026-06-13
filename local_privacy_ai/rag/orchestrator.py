from __future__ import annotations

import time
from dataclasses import dataclass

from local_privacy_ai.llm.ollama_client import OllamaClient
from local_privacy_ai.rag.prompt_builder import build_prompt
from local_privacy_ai.storage.chroma_store import ChromaStore


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    sources: list[dict]
    latency_ms: int


class RAGOrchestrator:
    def __init__(self, store: ChromaStore, llm: OllamaClient, top_k: int = 5) -> None:
        self.store = store
        self.llm = llm
        self.top_k = top_k

    async def answer(self, query: str, top_k: int | None = None) -> AnswerResult:
        started = time.perf_counter()
        sources = self.store.search(query, k=top_k or self.top_k)
        prompt = build_prompt(query, sources)
        answer = await self.llm.generate(prompt)
        latency_ms = int((time.perf_counter() - started) * 1000)
        return AnswerResult(answer=answer, sources=sources, latency_ms=latency_ms)
