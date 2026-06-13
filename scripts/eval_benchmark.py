from __future__ import annotations

import argparse
import asyncio
import csv
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from local_privacy_ai.app_factory import build_orchestrator


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run local RAG benchmark questions.")
    parser.add_argument("--questions", default="data/benchmark_questions.json")
    parser.add_argument("--output", default="reports/results/local_benchmark.csv")
    args = parser.parse_args()

    questions_path = Path(args.questions)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    questions = json.loads(questions_path.read_text(encoding="utf-8"))
    if not questions:
        raise SystemExit(f"No benchmark questions found in {questions_path}")

    orchestrator = build_orchestrator()

    rows = []
    for item in questions:
        result = await orchestrator.answer(item["question"])
        rows.append(
            {
                "id": item["id"],
                "category": item.get("category", ""),
                "question": item["question"],
                "expected_answer": item.get("expected_answer", ""),
                "answer": result.answer,
                "latency_ms": result.latency_ms,
                "source_count": len(result.sources),
                "manual_score": "",
                "notes": "",
            }
        )
        print(f"{item['id']}: {result.latency_ms} ms")

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    latencies = [int(row["latency_ms"]) for row in rows]
    print(f"Wrote {output_path}")
    print(f"Mean latency: {statistics.mean(latencies):.0f} ms")
    print(f"Median latency: {statistics.median(latencies):.0f} ms")


if __name__ == "__main__":
    asyncio.run(main())
