# Phase 3 results summary

This file summarizes the current empirical evidence for the Phase 3 report.
Detailed local CSV/JSON files are stored under `reports/results/` and are not
tracked in Git because they may contain private smart-home context.

## Local benchmark

- Benchmark size: 30 questions.
- Categories: temperature, motion, illuminance, energy, device state, and
  insufficient-context cases.
- Model: local Ollama model configured through `.env`.
- Data source: Home Assistant history from the selected local entities.
- Vector store: ChromaDB with per-hour chunks and per-entity aggregate summary
  chunks.
- Final scored run: `reports/results/local_benchmark_30_final_scored.csv`.
- Manual score: 56/60 points, or 93.3%.
- Mean latency: 6284 ms.
- Median latency: 5713 ms.
- Timeouts/errors: 0.

The scoring uses a simple 0-2 rubric:

- 2: correct and sufficiently specific answer.
- 1: partially correct answer, such as correct conclusion with missing count or
  timestamp detail.
- 0: incorrect, unsupported, or missing answer.

## Privacy audit

- Audit script: `scripts/privacy_connection_audit.py`.
- Query set: `reports/results/privacy_queries.local.json`.
- Offline flags: `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1`.
- Scope: benchmark process and local Ollama process.
- Samples: 74.
- External IP observations for monitored processes: 0.
- Benchmark exit code: 0.
- Result files:
  - `reports/results/privacy_connection_audit_scoped.json`
  - `reports/results/privacy_connection_audit_scoped_benchmark.csv`

This process-level audit supports the privacy claim, but the final report should
also include, or explicitly discuss the limitation of not including, a full
`sudo tcpdump` packet capture on `en0`.

## Current limitation notes

- The benchmark uses a 24-hour Home Assistant capture, so results describe that
  window rather than the full lifetime of the smart-home system.
- Some aggregate questions are answered from generated summary chunks, not only
  raw event chunks. This should be described as part of the retrieval design.
- The process-level privacy audit does not capture all packets on the interface;
  it monitors relevant process connections. A packet capture is stronger.
