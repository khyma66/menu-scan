import asyncio
import inspect
import json
from gemini_ocr import run_gemini_menu_ocr
from embeddings import get_embedding
from supabase_db import SupabaseDB
from r2_store import R2Store

async def process_job(job_payload, db, r2):
    job_id = job_payload["job_id"]
    user_id = job_payload["user_id"]
    user_country = job_payload["user_country"]
    target_lang = job_payload["target_lang"]
    r2_keys = job_payload["r2_keys"]
    job_restaurant_name = job_payload.get("restaurant_name")
    job_region = job_payload.get("region")
    job_cuisine = job_payload.get("cuisine_type")

    try:
        await db.update_job(job_id, status="processing")

        image_bytes_list = []
        for key in r2_keys:
            image_bytes_list.append(await r2.download(key))

        health_profile = await db.get_health_profile(user_id)

        result = await run_gemini_menu_ocr(
            image_bytes_list=image_bytes_list,
            target_lang=target_lang,
            user_country=user_country,
            health_profile=health_profile,
        )

        restaurant_name = job_restaurant_name or result.get("restaurant_name") or "Unknown"
        region = job_region or result.get("region") or user_country
        cuisine_type = job_cuisine or result.get("cuisine_type")
        ocr_raw = result.get("ocr_raw", "")
        currency = result.get("currency")

        menu = await db.create_menu(
            user_id=user_id,
            restaurant_name=restaurant_name,
            region=region,
            cuisine_type=cuisine_type,
            r2_image_keys=r2_keys,
            ocr_raw=ocr_raw,
        )

        for dish in result.get("dishes", []):
            name = dish.get("name")
            if not name:
                continue

            ingredients = dish.get("ingredients") or []
            ingredients_raw = ", ".join([i.get("name") for i in ingredients if i.get("name")])

            nutrition = dish.get("nutrition_per_serving") or {}
            flags = dish.get("flags") or {}
            recommendation = dish.get("health_recommendation") or {}

            embedding_text = " ".join([name, dish.get("description") or "", ingredients_raw]).strip()
            embedding = await get_embedding(embedding_text) if embedding_text else None

            dish_record = await db.create_dish(
                menu_id=menu.get("id"),
                user_id=user_id,
                dish={
                    "name": name,
                    "description": dish.get("description"),
                    "price": dish.get("price"),
                    "currency": currency or dish.get("currency"),
                    "category": dish.get("category"),
                    "ingredients_raw": ingredients_raw,
                    "ingredients_json": {"items": ingredients},
                    "calories": nutrition.get("calories"),
                    "protein_g": nutrition.get("protein_g"),
                    "fat_g": nutrition.get("fat_g"),
                    "carbs_g": nutrition.get("carbs_g"),
                    "fiber_g": nutrition.get("fiber_g"),
                    "sugar_g": nutrition.get("sugar_g"),
                    "sodium_mg": nutrition.get("sodium_mg"),
                    "cholesterol_mg": nutrition.get("cholesterol_mg"),
                    "is_vegetarian": flags.get("is_vegetarian"),
                    "is_vegan": flags.get("is_vegan"),
                    "contains_dairy": flags.get("contains_dairy"),
                    "contains_gluten": flags.get("contains_gluten"),
                    "contains_nuts": flags.get("contains_nuts"),
                    "contains_shellfish": flags.get("contains_shellfish"),
                    "health_score": dish.get("health_score"),
                    "embedding": embedding,
                },
            )

            await db.create_recommendation(
                dish_record.get("id"),
                user_id,
                {
                    "level": recommendation.get("level"),
                    "summary": recommendation.get("summary"),
                    "trigger_ingredients": recommendation.get("trigger_ingredients"),
                    "alternative_suggestion": recommendation.get("alternative_suggestion"),
                    "alternative_dish_name": recommendation.get("alternative_dish_name"),
                    "triggered_health_conditions": recommendation.get("triggered_health_conditions"),
                    "gemini_analysis": recommendation,
                },
            )

        await db.update_job(job_id, status="done", menu_id=menu.get("id"))
        return {"status": "done", "menu_id": menu.get("id")}
    except Exception as exc:
        await db.update_job(job_id, status="failed", error=str(exc))
        raise

async def handle_messages(messages):
    db = SupabaseDB()
    r2 = R2Store()
    await asyncio.gather(*[process_job(msg, db, r2) for msg in messages])


def _message_body(message):
    if isinstance(message, dict) and "body" in message:
        return message["body"]
    if hasattr(message, "body"):
        return message.body
    return message


async def _ack_message(message):
    ack = getattr(message, "ack", None)
    if not ack:
        return
    result = ack()
    if inspect.isawaitable(result):
        await result


async def queue(batch, env):
    messages = [_message_body(msg) for msg in batch.messages]
    await handle_messages(messages)
    for msg in batch.messages:
        await _ack_message(msg)

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        raise SystemExit("Usage: python consumer.py <job_payload.json>")

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        payload = json.load(f)
    asyncio.run(handle_messages([payload]))
