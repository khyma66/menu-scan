import base64
import json
import os
import re
import logging
import httpx

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_API_BASE = os.getenv("GEMINI_API_BASE", "https://generativelanguage.googleapis.com/v1beta")
GEMINI_TIMEOUT = float(os.getenv("GEMINI_TIMEOUT", "60"))
GEMINI_LOG_PROMPT = os.getenv("GEMINI_LOG_PROMPT", "false").lower() == "true"

logger = logging.getLogger(__name__)

JSON_FENCE_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def _build_prompt(target_lang: str, user_country: str, health_profile: dict | None) -> str:
    conditions = ", ".join(health_profile.get("health_conditions", [])) if health_profile else "None"
    allergies = ", ".join(health_profile.get("allergies", [])) if health_profile else "None"
    prefs = ", ".join(health_profile.get("dietary_preferences", [])) if health_profile else "None"
    notes = health_profile.get("medical_notes") if health_profile else None
    notes_text = notes or "None"

    return (
        "You are a restaurant menu OCR specialist with expertise in nutrition, ingredients, and health analysis.\n\n"
        "USER HEALTH PROFILE:\n"
        f"- Health Conditions: {conditions}\n"
        f"- Allergies: {allergies}\n"
        f"- Dietary Preferences: {prefs}\n"
        f"- Medical Notes: {notes_text}\n"
        f"- Country: {user_country}\n\n"
        "Return a single JSON object with these top-level keys:\n"
        '"restaurant_name", "region", "cuisine_type", "currency", "ocr_raw", "dishes".\n\n'
        "Each dish must include:\n"
        "{\n"
        '  "name": "Dish name",\n'
        '  "description": "Dish description"|null,\n'
        '  "price": 12.5|null,\n'
        '  "category": "Category"|null,\n'
        '  "ingredients": [\n'
        '    {"name": "ingredient", "quantity": "50g", "note": "allergen/health note"}\n'
        "  ],\n"
        '  "nutrition_per_serving": {\n'
        '    "calories": 650, "protein_g": 28, "fat_g": 48, "carbs_g": 35,\n'
        '    "fiber_g": 2, "sugar_g": 1, "sodium_mg": 800, "cholesterol_mg": 220\n'
        "  },\n"
        '  "flags": {\n'
        '    "is_vegetarian": false, "is_vegan": false, "contains_dairy": true,\n'
        '    "contains_gluten": true, "contains_nuts": false, "contains_shellfish": false\n'
        "  },\n"
        '  "health_score": 0.45,\n'
        '  "health_recommendation": {\n'
        '    "level": "safe|caution|avoid",\n'
        '    "summary": "Why",\n'
        '    "trigger_ingredients": [\n'
        '      {"name": "cream", "reason": "High lactose", "risk_level": "severe", "triggered_condition": "lactose intolerance"}\n'
        "    ],\n"
        '    "triggered_health_conditions": ["lactose intolerance"],\n'
        '    "alternative_suggestion": "Try a dairy-free option",\n'
        '    "alternative_dish_name": "Aglio e Olio"\n'
        "  }\n"
        "}\n\n"
        "Requirements:\n"
        "- Extract all menu items, ingredients, and prices.\n"
        f"- Translate all text fields to language: {target_lang}.\n"
        "- Estimate nutrition values per serving.\n"
        "- Generate health recommendations based on the user profile.\n"
        "- Output only JSON, no extra text.\n"
    )


def _extract_json(text: str) -> dict:
    if not text:
        raise ValueError("Empty Gemini response")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fence_match = JSON_FENCE_RE.search(text)
    if fence_match:
        return json.loads(fence_match.group(1))

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])

    raise ValueError("Unable to parse JSON from Gemini response")


def _normalize_result(data: dict, user_country: str) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Gemini JSON must be an object")

    dishes = data.get("dishes") if isinstance(data.get("dishes"), list) else []

    return {
        "restaurant_name": data.get("restaurant_name"),
        "region": data.get("region"),
        "cuisine_type": data.get("cuisine_type"),
        "currency": data.get("currency"),
        "ocr_raw": data.get("ocr_raw") or "",
        "dishes": dishes,
    }


async def run_gemini_menu_ocr(image_bytes_list, target_lang: str, user_country: str, health_profile: dict | None) -> dict:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    prompt = _build_prompt(target_lang, user_country, health_profile)
    logger.info("Gemini request model=%s target_lang=%s country=%s images=%s", GEMINI_MODEL, target_lang, user_country, len(image_bytes_list))
    if GEMINI_LOG_PROMPT:
        logger.info("Gemini prompt(full): %s", prompt)
    else:
        logger.info("Gemini prompt(snippet): %s", prompt[:400].replace("\n", " "))

    image_parts = []
    for image_bytes in image_bytes_list:
        image_parts.append(
            {
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(image_bytes).decode("ascii"),
                }
            }
        )

    payload = {
        "contents": [
            {
                "role": "user",
                    "parts": [{"text": prompt}, *image_parts],
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "response_mime_type": "application/json",
        },
    }

    url = f"{GEMINI_API_BASE}/models/{GEMINI_MODEL}:generateContent"

    async with httpx.AsyncClient(timeout=GEMINI_TIMEOUT) as client:
        resp = await client.post(url, params={"key": GEMINI_API_KEY}, json=payload)
        resp.raise_for_status()
        data = resp.json()

    candidates = data.get("candidates") or []
    if not candidates:
        raise ValueError("Gemini returned no candidates")

    parts = (candidates[0].get("content") or {}).get("parts") or []
    text = ""
    for part in parts:
        if "text" in part:
            text += part["text"]

    parsed = _extract_json(text)
    return _normalize_result(parsed, user_country)
