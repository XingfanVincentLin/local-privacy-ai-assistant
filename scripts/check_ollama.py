from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from local_privacy_ai.config import Settings
from local_privacy_ai.llm.ollama_client import OllamaClient


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run a tiny Ollama generation smoke test.")
    parser.add_argument("--prompt", default="Answer in one short sentence: what is Home Assistant?")
    args = parser.parse_args()

    settings = Settings.from_env()
    client = OllamaClient(settings.ollama_host, settings.ollama_model)
    answer = await client.generate(args.prompt)
    print(answer)


if __name__ == "__main__":
    asyncio.run(main())
