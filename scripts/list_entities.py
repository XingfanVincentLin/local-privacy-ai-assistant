from __future__ import annotations

import argparse
import asyncio
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from local_privacy_ai.config import Settings
from local_privacy_ai.ingestion.ha_client import HomeAssistantClient


async def main() -> None:
    parser = argparse.ArgumentParser(description="List Home Assistant entities for benchmark setup.")
    parser.add_argument("--output", default="reports/results/ha_entities.csv")
    parser.add_argument(
        "--domains",
        default="sensor,binary_sensor,switch,light",
        help="Comma-separated domains to include.",
    )
    args = parser.parse_args()

    settings = Settings.from_env()
    settings.validate_for_ingestion()

    domains = {domain.strip() for domain in args.domains.split(",") if domain.strip()}
    client = HomeAssistantClient(settings.ha_base_url, settings.ha_token)
    states = await client.get_states()

    rows = []
    for item in states:
        entity_id = str(item.get("entity_id", ""))
        domain = entity_id.split(".", 1)[0] if "." in entity_id else ""
        if domains and domain not in domains:
            continue
        attributes = item.get("attributes") or {}
        rows.append(
            {
                "entity_id": entity_id,
                "domain": domain,
                "friendly_name": attributes.get("friendly_name", ""),
                "state": item.get("state", ""),
                "unit": attributes.get("unit_of_measurement", ""),
                "device_class": attributes.get("device_class", ""),
            }
        )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["entity_id", "domain", "friendly_name", "state", "unit", "device_class"],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} entities to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
