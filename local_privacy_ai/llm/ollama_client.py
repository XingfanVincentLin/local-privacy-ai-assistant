from __future__ import annotations

import httpx


class OllamaClient:
    def __init__(self, host: str, model: str, timeout: float = 120.0) -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 350,
            },
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.host}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            return str(data.get("response", "")).strip()

