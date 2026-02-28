import hashlib
from embeddings import get_embedding

SIMILARITY_MIN = 0.75

async def find_similar_dishes(table_json, user_country, target_lang, db):
    results = []

    for section in table_json.get("sections", []):
        for item in section.get("items", []):
            text = " ".join([item.get("name") or "", item.get("description") or ""]).strip()
            if not text:
                continue

            query_key = hashlib.sha256(f"{user_country}:{text}".encode("utf-8")).hexdigest()
            cached = await db.get_cache(query_key, user_country)
            if cached:
                results.append({
                    "dish": item.get("name"),
                    "country": user_country,
                    "matches": cached.get("results_json"),
                    "source": "cache",
                })
                continue

            embedding = await get_embedding(text)
            if not embedding:
                continue

            matches = await db.match_country_dishes(embedding, user_country, limit_count=5)
            filtered = [m for m in matches if m.get("similarity", 0) >= SIMILARITY_MIN]

            if filtered:
                results.append({
                    "dish": item.get("name"),
                    "country": user_country,
                    "matches": filtered,
                    "source": "supabase",
                })
                await db.set_cache(user_country, query_key, filtered, source_urls=[], embedding=embedding)

    return results
