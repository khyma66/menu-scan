import os
import httpx

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))

async def get_embedding(text):
    if not GEMINI_API_KEY:
        return None

    url = "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedText"
    payload = {"text": text}

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(f"{url}?key={GEMINI_API_KEY}", json=payload)
        resp.raise_for_status()
        data = resp.json()
        values = data.get("embedding", {}).get("values")
        if not values:
            return None
        if len(values) == EMBEDDING_DIM:
            return values
        if len(values) > EMBEDDING_DIM:
            return values[:EMBEDDING_DIM]
        return values + [0.0] * (EMBEDDING_DIM - len(values))
