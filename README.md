# Local Privacy AI Assistant

A privacy-preserving personal AI assistant that runs entirely on local hardware.
A client-server RAG (Retrieval-Augmented Generation) system for querying smart
home data and personal files using natural language — without any cloud
dependency.

> Academic project for IU Internationale Hochschule, Course DLMCSPCSP01 (Project:
> Computer Science Project). Author: Xingfan Lin (IU14140678).

## Overview

This system answers natural-language questions about a user's own personal data
(Home Assistant sensor history, CSV exports, documents) entirely on local
hardware — a Raspberry Pi 5 or an Apple Silicon MacBook Air. No data leaves the
home network.

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

See the project report PDF for full architecture, RAG pipeline, and component
interaction diagrams.

## Tech stack

- **LLM runtime:** Ollama (running Llama 3.2 3B or Phi-3 Mini)
- **Embeddings:** sentence-transformers (`all-MiniLM-L6-v2`)
- **Vector DB:** ChromaDB
- **Backend:** FastAPI
- **Frontend:** Vanilla HTML + JavaScript
- **Language:** Python 3.11+
- **Hosting:** Raspberry Pi 5 (8 GB) or Apple Silicon Mac

## Status

This is an academic work-in-progress. As of Phase 2 (May 2026), the environment
is set up and the core pipeline scaffolding is in place. The FastAPI server,
web UI, and full evaluation harness will be completed for Phase 3.

## Installation (preliminary)

```bash
# 1. Install Ollama (https://ollama.com) and pull a model
ollama pull llama3.2:3b

# 2. Clone the repo and set up the Python environment
git clone https://github.com/xingfan-lin/local-privacy-ai-assistant.git
cd local-privacy-ai-assistant
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Configure
cp config.yaml.example config.yaml
# Edit config.yaml with your Home Assistant URL and long-lived access token

# 4. Run the initial ingestion
python scripts/ingest_once.py

# 5. Start the server
uvicorn src.server.api:app --host 0.0.0.0 --port 8000
```

Open `http://<server-ip>:8000` in any browser on your home network.

## Repository structure

See the project report (Section 9.1) for the full source tree.

## Privacy guarantee

This system is designed and verified to make zero outbound network connections
during operation. The only external traffic occurs during initial setup (model
and dependency downloads). Verification is performed via `tcpdump` packet
captures on the server interface during a 30-minute query session — see Phase
3 evaluation results.

## Licence

MIT (planned for final release).

## Author

Xingfan Lin · Munich, Germany · IU Master's in Computer Science
