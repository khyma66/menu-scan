import os
import httpx

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


class SupabaseDB:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError("Supabase service role not configured")

    def _headers(self):
        return {
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
        }

    async def update_job(self, job_id, **updates):
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.patch(
                f"{SUPABASE_URL}/rest/v1/jobs?id=eq.{job_id}",
                headers=self._headers(),
                json=updates,
            )
            resp.raise_for_status()
            return True

    async def get_health_profile(self, user_id):
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{SUPABASE_URL}/rest/v1/user_health_profiles",
                headers=self._headers(),
                params={"user_id": f"eq.{user_id}", "select": "*"},
            )
            resp.raise_for_status()
            data = resp.json()
            return data[0] if data else None

    async def create_menu(self, user_id, restaurant_name, region, cuisine_type, r2_image_keys, ocr_raw):
        payload = {
            "user_id": user_id,
            "restaurant_name": restaurant_name,
            "region": region,
            "cuisine_type": cuisine_type,
            "r2_image_keys": r2_image_keys,
            "ocr_raw": ocr_raw,
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{SUPABASE_URL}/rest/v1/menus",
                headers={**self._headers(), "Prefer": "return=representation"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data[0] if data else payload

    async def create_dish(self, menu_id, user_id, dish):
        payload = {
            "menu_id": menu_id,
            "user_id": user_id,
            "name": dish.get("name"),
            "description": dish.get("description"),
            "price": dish.get("price"),
            "currency": dish.get("currency"),
            "category": dish.get("category"),
            "ingredients_raw": dish.get("ingredients_raw"),
            "ingredients_json": dish.get("ingredients_json"),
            "calories": dish.get("calories"),
            "protein_g": dish.get("protein_g"),
            "fat_g": dish.get("fat_g"),
            "carbs_g": dish.get("carbs_g"),
            "fiber_g": dish.get("fiber_g"),
            "sugar_g": dish.get("sugar_g"),
            "sodium_mg": dish.get("sodium_mg"),
            "cholesterol_mg": dish.get("cholesterol_mg"),
            "is_vegetarian": dish.get("is_vegetarian"),
            "is_vegan": dish.get("is_vegan"),
            "contains_dairy": dish.get("contains_dairy"),
            "contains_gluten": dish.get("contains_gluten"),
            "contains_nuts": dish.get("contains_nuts"),
            "contains_shellfish": dish.get("contains_shellfish"),
            "health_score": dish.get("health_score"),
            "embedding": dish.get("embedding"),
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{SUPABASE_URL}/rest/v1/dishes",
                headers={**self._headers(), "Prefer": "return=representation"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data[0] if data else payload

    async def create_recommendation(self, dish_id, user_id, rec):
        payload = {
            "dish_id": dish_id,
            "user_id": user_id,
            "recommendation_level": rec.get("level"),
            "risk_summary": rec.get("summary"),
            "trigger_ingredients": rec.get("trigger_ingredients"),
            "alternative_suggestion": rec.get("alternative_suggestion"),
            "alternative_dish_name": rec.get("alternative_dish_name"),
            "triggered_health_conditions": rec.get("triggered_health_conditions"),
            "gemini_analysis": rec.get("gemini_analysis"),
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{SUPABASE_URL}/rest/v1/dish_health_recommendations",
                headers=self._headers(),
                json=payload,
            )
            resp.raise_for_status()
            return True
