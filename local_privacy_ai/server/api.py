from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from local_privacy_ai.app_factory import build_default_orchestrator
from local_privacy_ai.config import Settings
from local_privacy_ai.ingestion.chunker import chunk_events_by_hour
from local_privacy_ai.ingestion.ha_client import HomeAssistantClient
from local_privacy_ai.ingestion.normalizer import normalize_history_payload
from local_privacy_ai.storage.chroma_store import ChromaStore
from local_privacy_ai.storage.embeddings import SentenceTransformerEmbedder

app = FastAPI(title="Local Privacy AI Assistant", version="0.1.0")


class AskRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)
    top_k: int = Field(default=5, ge=1, le=12)


class IngestRequest(BaseModel):
    hours: int = Field(default=24, ge=1, le=24 * 90)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ask")
async def ask(request: AskRequest) -> dict:
    orchestrator = build_default_orchestrator()
    try:
        result = await orchestrator.answer(request.query, top_k=request.top_k)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {
        "answer": result.answer,
        "latency_ms": result.latency_ms,
        "sources": result.sources,
    }


@app.post("/ingest")
async def ingest(request: IngestRequest) -> dict:
    settings = Settings.from_env()
    try:
        settings.validate_for_ingestion()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    client = HomeAssistantClient(settings.ha_base_url, settings.ha_token)
    try:
        payload = await client.get_history(hours=request.hours, entity_ids=settings.entity_ids)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Home Assistant request failed: {exc}") from exc
    events = normalize_history_payload(payload)
    chunks = chunk_events_by_hour(events)

    embedder = SentenceTransformerEmbedder()
    store = ChromaStore(settings.chroma_dir, settings.chroma_collection, embedder)
    inserted = store.upsert_chunks(chunks)
    return {
        "events": len(events),
        "chunks": inserted,
        "hours": request.hours,
    }


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Local Privacy AI Assistant</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 2rem; max-width: 900px; }
    textarea { width: 100%; min-height: 90px; font: inherit; padding: .75rem; }
    button { margin-top: .75rem; padding: .6rem 1rem; font: inherit; cursor: pointer; }
    pre { white-space: pre-wrap; background: #f5f5f5; padding: 1rem; border-radius: 8px; }
    .muted { color: #666; }
  </style>
</head>
<body>
  <h1>Local Privacy AI Assistant</h1>
  <p class="muted">Ask a question about locally ingested Home Assistant data.</p>
  <textarea id="query" placeholder="What was the average bedroom temperature yesterday evening?"></textarea>
  <br>
  <button id="ask">Ask locally</button>
  <p id="status" class="muted"></p>
  <h2>Answer</h2>
  <pre id="answer"></pre>
  <h2>Sources</h2>
  <pre id="sources"></pre>
  <script>
    document.getElementById("ask").addEventListener("click", async () => {
      const query = document.getElementById("query").value;
      document.getElementById("status").textContent = "Running local query...";
      document.getElementById("answer").textContent = "";
      document.getElementById("sources").textContent = "";
      const response = await fetch("/ask", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({query})
      });
      const data = await response.json();
      document.getElementById("status").textContent = `Latency: ${data.latency_ms || "n/a"} ms`;
      document.getElementById("answer").textContent = data.answer || JSON.stringify(data, null, 2);
      document.getElementById("sources").textContent = JSON.stringify(data.sources || [], null, 2);
    });
  </script>
</body>
</html>
"""
