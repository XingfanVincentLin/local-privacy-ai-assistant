# Local Privacy AI Assistant

A privacy-preserving personal AI assistant for querying Home Assistant data with
a local RAG (Retrieval-Augmented Generation) pipeline.

> Academic project for IU Internationale Hochschule, Course DLMCSPCSP01 (Project:
> Computer Science Project). Author: Xingfan Lin (IU14140678).

## Overview

This system answers natural-language questions about local smart home data
without sending the data to a cloud assistant. In the Phase 3 implementation,
Home Assistant remains on the Raspberry Pi 5 as the data source, while the
Apple Silicon MacBook Air runs the AI server, Ollama, ChromaDB, and the web UI.
All operational data flow stays inside the local network.

**Example queries:**

- "How much energy did I use last week?"
- "Was any motion detected overnight?"
- "What was the average bedroom temperature in May?"

## Architecture

```
+-----------------------+                +-----------------------+
|   Client (browser)    |  <-- HTTP -->  |  Personal AI Server   |
|  on home WiFi only    |                |  - FastAPI            |
+-----------------------+                |  - RAG orchestrator   |
                                         |  - Ollama (local LLM) |
                                         |  - ChromaDB           |
                                         |  - sentence-trans.    |
                                         +-----------------------+
                                                    |
                                                    | (LAN only)
                                                    v
                                         +-----------------------+
                                         |   Home Assistant      |
                                         |   REST API + sensors  |
                                         +-----------------------+
```

The Raspberry Pi keeps the existing Home Assistant setup stable. The MacBook is
used for local LLM inference because it is more practical for responsive model
generation during evaluation.

## Tech stack

- **LLM runtime:** Ollama (initial model: `qwen2.5:7b`)
- **Embeddings:** sentence-transformers (`all-MiniLM-L6-v2`)
- **Vector DB:** ChromaDB
- **Backend:** FastAPI
- **Frontend:** Vanilla HTML + JavaScript
- **Language:** Python 3.11+
- **Hosting:** Apple Silicon Mac for AI server; Raspberry Pi 5 for Home Assistant

## Status

This repository now contains the Phase 3 implementation scaffold:

- Home Assistant REST history ingestion
- sensor event normalization and chunking
- ChromaDB storage
- sentence-transformers embeddings
- Ollama-based RAG orchestration
- FastAPI API and simple local web UI
- benchmark, entity inventory, Ollama check, and ingestion scripts
- unit tests for the core pure-Python components

## Installation

```bash
# 1. Install Python 3.11+ if needed
brew install python@3.11

# 2. Confirm Ollama is installed and the model is available
ollama list
# This project currently uses qwen2.5:7b.

# 3. Clone the repo and set up the Python environment
git clone https://github.com/XingfanVincentLin/local-privacy-ai-assistant.git
cd local-privacy-ai-assistant
/opt/homebrew/bin/python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

# 4. Configure local secrets
cp .env.example .env
# Edit .env with your Home Assistant URL and long-lived access token.
# Do not commit .env.

# 5. Run the initial ingestion
python scripts/list_entities.py
python scripts/ingest_once.py --hours 24

# 6. Start the server
python -m uvicorn local_privacy_ai.server.api:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000` in a browser on the Mac.

## Repository structure

- `local_privacy_ai/`: application package
- `scripts/`: ingestion and evaluation entry points
- `tests/`: unit tests
- `docs/`: Phase 3 workflow notes
- `data/benchmark_questions.example.json`: benchmark template

## Privacy guarantee

The system is designed so that normal query handling uses only the local Mac,
Ollama, local ChromaDB storage, and the Home Assistant API on the home network.
The final Phase 3 evaluation will verify this with packet capture during an
active query session. ChromaDB is configured with anonymized telemetry disabled.
Dependency downloads and model downloads are treated as setup steps, not part of
normal operation.

## Running tests

```bash
pip install -r requirements-dev.txt
pytest
```

## Useful scripts

```bash
# Confirm the selected local Ollama model responds
python scripts/check_ollama.py

# Export a CSV inventory of useful Home Assistant entities
python scripts/list_entities.py

# Ingest recent Home Assistant history into ChromaDB
python scripts/ingest_once.py --hours 24

# Run benchmark questions after data has been ingested
python scripts/eval_benchmark.py --questions data/benchmark_questions.json
```

## Author

Xingfan Lin, Munich, Germany. IU Master's in Computer Science.
