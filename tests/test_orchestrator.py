from __future__ import annotations

import pytest

from local_privacy_ai.rag.orchestrator import RAGOrchestrator


class FakeStore:
    def __init__(self) -> None:
        self.last_k = None

    def search(self, query: str, k: int = 5) -> list[dict]:
        self.last_k = k
        return [{"text": f"Context for {query}", "metadata": {}, "distance": 0.1}]


class FakeLLM:
    async def generate(self, prompt: str) -> str:
        assert "Context for" in prompt
        return "The answer is grounded in the retrieved context."


@pytest.mark.anyio
async def test_orchestrator_returns_answer_sources_and_latency() -> None:
    store = FakeStore()
    orchestrator = RAGOrchestrator(store=store, llm=FakeLLM())

    result = await orchestrator.answer("test question", top_k=3)

    assert result.answer == "The answer is grounded in the retrieved context."
    assert len(result.sources) == 1
    assert result.latency_ms >= 0
    assert store.last_k == 3
