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


FIELDNAMES = [
    "id",
    "category",
    "question",
    "expected_answer",
    "answer",
    "latency_ms",
    "source_count",
    "source_entities",
    "source_ids",
    "manual_score",
    "notes",
]


def write_rows(output_path: Path, rows: list[dict]) -> None:
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run local RAG benchmark questions.")
    parser.add_argument("--questions", default="data/benchmark_questions.json")
    parser.add_argument("--output", default="reports/results/local_benchmark.csv")
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=45.0,
        help="Maximum time allowed for one benchmark question.",
    )
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
        notes = ""
        try:
            result = await asyncio.wait_for(
                orchestrator.answer(item["question"]),
                timeout=args.timeout_seconds,
            )
            answer = result.answer
            latency_ms = result.latency_ms
            source_ids = [source["id"] for source in result.sources]
            source_entities = [
                str(source.get("metadata", {}).get("entity_id", "")) for source in result.sources
            ]
        except TimeoutError:
            answer = f"ERROR: timed out after {args.timeout_seconds:.0f} seconds"
            latency_ms = int(args.timeout_seconds * 1000)
            source_ids = []
            source_entities = []
            notes = "timeout"
        except Exception as exc:
            answer = f"ERROR: {type(exc).__name__}: {exc}"
            latency_ms = ""
            source_ids = []
            source_entities = []
            notes = "error"

        rows.append(
            {
                "id": item["id"],
                "category": item.get("category", ""),
                "question": item["question"],
                "expected_answer": item.get("expected_answer", ""),
                "answer": answer,
                "latency_ms": latency_ms,
                "source_count": len(source_ids),
                "source_entities": "; ".join(source_entities),
                "source_ids": "; ".join(source_ids),
                "manual_score": "",
                "notes": notes,
            }
        )
        write_rows(output_path, rows)
        print(f"{item['id']}: {latency_ms} ms {notes}".strip(), flush=True)

    latencies = [int(row["latency_ms"]) for row in rows if str(row["latency_ms"]).isdigit()]
    print(f"Wrote {output_path}")
    print(f"Mean latency: {statistics.mean(latencies):.0f} ms")
    print(f"Median latency: {statistics.median(latencies):.0f} ms")


if __name__ == "__main__":
    asyncio.run(main())
