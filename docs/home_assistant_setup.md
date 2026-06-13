# Home Assistant setup

The project reads Home Assistant history from the Mac over the local network. The
Raspberry Pi Home Assistant installation does not need to be reinstalled or
changed for the first Phase 3 prototype.

## Long-lived access token

1. Open Home Assistant in the browser.
2. Go to the user profile page.
3. Create a long-lived access token.
4. Copy `.env.example` to `.env`.
5. Put the token into `HA_TOKEN` in `.env`.

Do not paste the token into chat and do not commit `.env`.

## Entity selection

Start with a small set of useful entities:

- temperature sensors
- IKEA motion or light sensors
- workstation smart plug energy/power sensors
- TV smart plug energy/power sensors
- important switch or light state entities

Add them to `HA_ENTITY_IDS` as a comma-separated list. Keeping the first run small
makes debugging easier and keeps the first ChromaDB collection readable.

## First test

```bash
python scripts/list_entities.py
python scripts/ingest_once.py --hours 24
python -m uvicorn local_privacy_ai.server.api:app --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000` on the Mac and ask a question about one of the
selected sensors.

The entity inventory is written to `reports/results/ha_entities.csv`. Use that
file to choose the exact entity IDs for `HA_ENTITY_IDS`.
