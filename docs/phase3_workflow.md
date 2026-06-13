# Phase 3 workflow

This document keeps the implementation and evaluation work aligned with the IU Phase 3
requirements.

## Local setup

1. Install Python 3.11 or newer.
2. Start Ollama and confirm `qwen2.5:7b` is available.
3. Copy `.env.example` to `.env`.
4. Add the Home Assistant base URL and a long-lived access token to `.env`.
5. Install dependencies in a virtual environment.
6. Run `python scripts/check_ollama.py` to confirm the local model responds.

## First end-to-end run

```bash
python scripts/list_entities.py
python scripts/ingest_once.py --hours 24
python -m uvicorn local_privacy_ai.server.api:app --reload
```

Open `http://127.0.0.1:8000` and ask one question about the ingested data.

## Evaluation notes

- Use roughly 30 benchmark questions for the lean final evaluation.
- Keep real Home Assistant data local.
- Use sanitized context for the cloud comparison.
- Record latency, answer quality, retrieved sources, and failure cases.
- Run a packet capture during local querying for the privacy proof.
