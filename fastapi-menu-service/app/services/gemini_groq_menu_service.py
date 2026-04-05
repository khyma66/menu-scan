"""Gemini OCR + Groq enhancement service for menu extraction."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_JSON_FENCE_RE = re.compile(r"```json\s*(\{.*?\}|\[.*?\])\s*```", re.DOTALL)
_PRICE_TOKEN_RE = re.compile(
    r"(?P<price>(?:[$€£¥₹]\s*\d+(?:[\.,]\d{1,2})?|\d+(?:[\.,]\d{1,2})?\s*(?:[$€£¥₹]|usd|eur|inr|aed|cad|aud)))",
    re.IGNORECASE,
)
_MAX_STRUCTURED_RETRIES = 3
_GEMINI_MAX_RETRIES = 3
_GEMINI_BACKOFF_BASE = 2.0  # seconds


class GeminiGroqMenuService:
    """Two-step pipeline:
    1) Gemini extracts clean English menu table rows from image.
    2) Groq enhances rows with taste, ingredients, similar dishes, and recommendation.
    """

    def __init__(self) -> None:
        self.gemini_api_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.gemini_model = settings.gemini_model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.gemini_api_base = settings.gemini_api_base or os.getenv(
            "GEMINI_API_BASE", "https://generativelanguage.googleapis.com/v1beta"
        )
        self.gemini_timeout = settings.gemini_timeout

        self.groq_api_key = settings.groq_api_key or os.getenv("GROQ_API_KEY")
        self.groq_model = settings.groq_model or os.getenv("GROQ_MODEL", "qwen/qwen3-32b")
        self.groq_api_base = settings.groq_api_base or os.getenv(
            "GROQ_API_BASE", "https://api.groq.com/openai/v1"
        )
        self.groq_timeout = settings.groq_timeout
        self._gemini_client = httpx.AsyncClient(timeout=self.gemini_timeout)
        self._groq_client = httpx.AsyncClient(timeout=self.groq_timeout)

        # Fallback enhancement providers (OpenAI / Anthropic via OpenAI-compat)
        self.openai_api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = settings.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.openrouter_api_key = settings.openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        self._fallback_client = httpx.AsyncClient(timeout=90.0)

        # Third model: Llama 3.3 70B on Groq for gap-filling
        self.llama_model = os.getenv("GROQ_LLAMA_MODEL", "llama-3.3-70b-versatile")

    def _extract_json(self, text: str) -> Any:
        if not text:
            raise ValueError("Empty model response")

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        fenced = _JSON_FENCE_RE.search(text)
        if fenced:
            return json.loads(fenced.group(1))

        start_obj = text.find("{")
        end_obj = text.rfind("}")
        if start_obj != -1 and end_obj != -1 and end_obj > start_obj:
            try:
                return json.loads(text[start_obj : end_obj + 1])
            except json.JSONDecodeError:
                pass

        start_arr = text.find("[")
        end_arr = text.rfind("]")
        if start_arr != -1 and end_arr != -1 and end_arr > start_arr:
            return json.loads(text[start_arr : end_arr + 1])

        raise ValueError("Could not parse JSON from model response")

    def _build_gemini_prompt(self, language_hint: str) -> str:
        return (
            "### ROLE\n"
            "You are an expert Data Extraction Specialist and OCR Engineer. Your task is to convert this menu image into a perfectly structured digital format.\n"
            "### PHASE 1: PRE-SCAN (Internal Reasoning)\n"
            "Before transcribing, mentally map image coordinates, identify headers/subheaders, and understand multi-column text-price relationships.\n"
            "### PHASE 2: ENGLISH-ONLY EXTRACTION RULES\n"
            "Translate the menu COMPLETELY into English. Every single dish from the image must be present in the final output.\n"
            "1) MANDATORY COVERAGE: Do not skip ANY item. If there are N dishes, output N dish rows.\n"
            "2) ENGLISH-ONLY: Do not include original-language dish text; output high-quality English for dish names, descriptions, and category headers.\n"
            "3) SYMBOL FIDELITY: Retain currency symbols (€,$,£,¥), allergen numbers (e.g., 1,7,8), and units (e.g., €/hg) exactly where visible.\n"
            "4) CULINARY ACCURACY: Translate culinary terms accurately in natural English.\n"
            "5) ACCURACY OVER SPEED: If ambiguous, reason conservatively; use [?] only if truly unreadable.\n"
            "### PHASE 3: OUTPUT FORMAT\n"
            "The application requires strict JSON (not markdown). Preserve menu structure using category field.\n"
            "### PHASE 4: FOOTER EXTRACTION\n"
            "Capture all fine print (taxes, service charge, bread cover, policy notes) as explicit rows if visible.\n"
            "### FINAL STEP\n"
            "Verify output item count matches visible image items before returning.\n"
            "Output must be strict JSON only. No markdown, no commentary.\n\n"
            "Return this exact structure:\n"
            "{\n"
            '  "menu_items": [\n'
            "    {\n"
            '      "item": "Dish name in English",\n'
            '      "description_ingredients": "Short description and key ingredients in English",\n'
            '      "price": "Original menu price string",\n'
            '      "currency": "ISO code if known else null",\n'
            '      "category": "section heading like Antipasti/Primi piatti or normalized category if heading not visible"\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            "Rules:\n"
            "- Do not omit any visible item row.\n"
            "- Preserve visual reading order (top->bottom, left->right by column).\n"
            "- Keep section/subsection meaning in category field.\n"
            "- Include footer/service/bread/cover notes as rows when present.\n"
            "- Keep one row per purchasable item or explicit pricing note.\n"
            "- Sweep the entire image in this order: top-left -> top-right -> middle-left -> middle-right -> bottom-left -> bottom-right.\n"
            "- item must contain only dish/note name; never include price tokens in item.\n"
            "- price must contain only the original visible price string/symbols; if absent use null.\n"
            "- description_ingredients should include visible description/allergen/unit context; if unknown use null.\n"
            "- If a field is unknown, use null (not empty string).\n"
            "- Never output sample items unless visibly present in image.\n"
            "- If the image is unreadable, return {\"menu_items\": []}.\n"
            "- language_hint from client: "
            f"{language_hint}.\n"
        )

    def _build_gemini_second_pass_prompt(self, language_hint: str, existing_names: List[str]) -> str:
        return (
            "Re-check the same menu image as a strict OCR auditor for missed items.\n"
            "Goal: produce a COMPLETE list of all visible menu rows, especially under subsection headers, side columns, and footer notes.\n"
            "Current extracted names (may be incomplete): "
            f"{json.dumps(existing_names, ensure_ascii=False)}\n"
            "Return strict JSON only with schema {\"menu_items\":[{\"item\",\"description_ingredients\",\"price\",\"currency\",\"category\"}]}.\n"
            "Rules:\n"
            "- Keep every visible row exactly once.\n"
            "- Add rows that were missed in the first pass.\n"
            "- Include service/bread/cover/footer pricing notes as rows if visible.\n"
            "- Preserve symbols like €, parenthesized allergen numbers, and units like €/hg.\n"
            "- item must not include any price token.\n"
            "- price must contain the visible price token only.\n"
            "- Do not invent sample/common dishes.\n"
            "- If unreadable, return {\"menu_items\": []}.\n"
            f"- language_hint from client: {language_hint}.\n"
        )

    async def _call_gemini(self, prompt: str, image_bytes: bytes) -> Dict[str, Any]:
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": base64.b64encode(image_bytes).decode("ascii"),
                            }
                        },
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0.0,
                "response_mime_type": "application/json",
            },
        }

        url = f"{self.gemini_api_base}/models/{self.gemini_model}:generateContent"
        last_exc: Optional[Exception] = None

        for attempt in range(1, _GEMINI_MAX_RETRIES + 1):
            try:
                logger.info("Gemini extraction request model=%s attempt=%s/%s", self.gemini_model, attempt, _GEMINI_MAX_RETRIES)
                resp = await self._gemini_client.post(url, params={"key": self.gemini_api_key}, json=payload)
                resp.raise_for_status()
                data = resp.json()

                candidates = data.get("candidates") or []
                if not candidates:
                    raise ValueError("Gemini returned no candidates")

                text = ""
                for part in ((candidates[0].get("content") or {}).get("parts") or []):
                    if "text" in part:
                        text += part["text"]

                parsed = self._extract_json(text)
                if not isinstance(parsed, dict):
                    raise ValueError("Gemini extraction output must be a JSON object")

                rows = parsed.get("menu_items") if isinstance(parsed.get("menu_items"), list) else []
                return {"menu_items": rows, "raw_text": text}

            except Exception as exc:
                last_exc = exc
                if attempt < _GEMINI_MAX_RETRIES:
                    wait = _GEMINI_BACKOFF_BASE ** attempt
                    logger.warning("Gemini call failed attempt=%s/%s error=%s retrying_in=%.1fs", attempt, _GEMINI_MAX_RETRIES, exc, wait)
                    await asyncio.sleep(wait)

        raise last_exc or RuntimeError("Gemini call failed after retries")

    def _merge_unique_rows(self, first: List[Dict[str, Any]], second: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        merged: List[Dict[str, Any]] = []
        seen = set()

        for row in first + second:
            identity = self._row_identity(row)
            if not identity[0]:
                continue
            if identity in seen:
                continue
            seen.add(identity)
            merged.append(row)

        return merged

    def _norm_name(self, value: Any) -> str:
        return str(value or "").strip().lower()

    def _row_identity(self, row: Dict[str, Any]) -> tuple[str, str]:
        item = self._norm_name(row.get("item"))
        price = str(row.get("price") or "").strip().lower()
        return (item, price)

    def _build_groq_prompt(self, extracted_rows: List[Dict[str, Any]], health_profile: Dict[str, Any]) -> str:
        menu_names = [str(row.get("item") or "").strip() for row in extracted_rows if str(row.get("item") or "").strip()]
        return (
            "You are an expert culinary knowledge agent that enhances OCR-extracted menu rows.\n"
            "For EVERY field in EVERY dish, you MUST use your real-world culinary knowledge to provide accurate, "
            "dish-specific information — as if you looked up each dish on a food encyclopedia or culinary database.\n\n"
            "Health profile:\n"
            f"{json.dumps(health_profile, ensure_ascii=False)}\n\n"
            "Current menu dish names (do NOT use these as similar dishes):\n"
            f"{json.dumps(menu_names, ensure_ascii=False)}\n\n"
            "Input rows:\n"
            f"{json.dumps(extracted_rows, ensure_ascii=False)}\n\n"
            "Return strict JSON only with this shape:\n"
            "{\n"
            '  "menu_items": [\n'
            "    {\n"
            '      "item": "Dish name in English",\n'
            '      "description_ingredients": "A vivid 1-2 sentence description of what this specific dish is",\n'
            '      "price": "Price string or null",\n'
            '      "ingredients": ["ingredient1", "ingredient2", "...at least 5 real ingredients"],\n'
            '      "taste": "spicy|salty|tangy|sweet|savory|umami|mild|mixed",\n'
            '      "similarDish1": "A well-known dish from ANOTHER cuisine with similar flavors",\n'
            '      "similarDish2": "Another well-known dish from a DIFFERENT cuisine",\n'
            '      "recommendation": "Most Recommended|Recommended|Not Recommended",\n'
            '      "recommendation_reason": "Short reason tied to health profile",\n'
            '      "category": "appetizer|main|dessert|drink|side|other",\n'
            '      "allergens": ["gluten", "dairy", "nuts"],\n'
            '      "spiciness_level": "none|mild|medium|hot|extra hot",\n'
            '      "preparation_method": "grilled|fried|baked|steamed|raw|sautéed|roasted|boiled|other"\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            "CRITICAL KNOWLEDGE-LOOKUP RULES — apply to EVERY dish:\n"
            "- description_ingredients: Write a UNIQUE, tailored description for THIS specific dish — mention its cuisine origin, "
            "key flavors, and what makes it distinctive. Each dish MUST have a different description. "
            "If the menu provides no description, use your culinary knowledge to describe what the dish traditionally is, "
            "its origin, and what makes it distinctive. NEVER use generic filler like 'a thoughtfully prepared dish' or "
            "'a popular menu item'. Every description must be specific enough that a reader can identify the dish from it alone.\n"
            "- ingredients: List the REAL, specific ingredients used in this dish as traditionally prepared. "
            "Include proteins, vegetables, sauces, spices, and base ingredients. "
            "Minimum 5 ingredients per dish. If the menu text lists ingredients, use those AND supplement with "
            "commonly known additional ingredients. If the menu does NOT list ingredients, infer ALL typical ingredients "
            "from your knowledge of the dish's cuisine and cooking tradition.\n"
            "- taste: Identify the PRIMARY taste profile of this specific dish based on its known flavor. "
            "A Pad Thai is 'tangy', a Tiramisu is 'sweet', a Kimchi Jjigae is 'spicy'. Be dish-specific.\n"
            "- similarDish1 / similarDish2: Name two REAL, internationally recognized dishes from OTHER cuisines "
            "that share flavor profiles or preparation style. Be specific — not generic categories. "
            "e.g., for Butter Chicken → 'Japanese Katsu Curry' and 'Moroccan Chicken Tagine'.\n"
            "- allergens: Identify REAL allergens based on the dish's actual ingredients "
            "(gluten, dairy, nuts, shellfish, eggs, soy, fish, peanuts, sesame, celery, mustard, sulfites). "
            "A pizza has [gluten, dairy]. A pad thai has [peanuts, soy, eggs, shellfish]. Be accurate.\n"
            "- spiciness_level: Rate based on the dish's known heat level in its traditional preparation.\n"
            "- preparation_method: Identify the PRIMARY cooking method for this dish as traditionally made.\n"
            "- category: Classify accurately — a French Fries is 'side', a Coke is 'drink', Tiramisu is 'dessert'.\n\n"
            "STRUCTURAL RULES:\n"
            "- Output row count MUST equal input row count exactly.\n"
            "- Preserve row order exactly; output row i corresponds to input row i.\n"
            "- Never drop, merge, or deduplicate rows.\n"
            "- item must contain only the dish name; never put price/currency into item.\n"
            "- price must remain in price field only.\n"
            "- recommendation must be exactly one of: Most Recommended, Recommended, Not Recommended.\n"
            "- Use health profile (allergies/conditions/preferences) for recommendation.\n"
            "- If health profile has NO conditions/allergies/preferences, set recommendation and recommendation_reason to null.\n"
            "- similarDish1 and similarDish2 must NOT be from the current input menu and must NOT match the item itself.\n"
            "- Keep outputs in English.\n"
        )

    def _build_groq_repair_prompt(
        self,
        extracted_rows: List[Dict[str, Any]],
        health_profile: Dict[str, Any],
        previous_rows: List[Dict[str, Any]],
        validation_error: str,
    ) -> str:
        return (
            "Fix the previous enhancement output. Return strict JSON only.\n"
            f"Validation error to fix: {validation_error}\n\n"
            "Input rows (must be preserved in count and order):\n"
            f"{json.dumps(extracted_rows, ensure_ascii=False)}\n\n"
            "Health profile:\n"
            f"{json.dumps(health_profile, ensure_ascii=False)}\n\n"
            "Previous invalid output:\n"
            f"{json.dumps(previous_rows, ensure_ascii=False)}\n\n"
            "Required output schema: {\"menu_items\":[{\"item\",\"description_ingredients\",\"price\",\"ingredients\",\"taste\",\"similarDish1\",\"similarDish2\",\"recommendation\",\"recommendation_reason\",\"category\",\"allergens\",\"spiciness_level\",\"preparation_method\"}]}\n"
            "Rules:\n"
            "- menu_items length must exactly equal input rows length.\n"
            "- Output row i must correspond to input row i.\n"
            "- Never drop or merge rows.\n"
            "- item must be non-empty and must not contain price tokens.\n"
            "- Fill all enrichment fields with best-effort inference when missing.\n"
        )

    def _build_translation_prompt(self, menu_items: List[Dict[str, Any]], target_language: str) -> str:
        return (
            "Translate each menu row to the requested language while preserving structure.\n"
            "Target language: " + target_language + "\n"
            "Input rows:\n"
            f"{json.dumps(menu_items, ensure_ascii=False)}\n\n"
            "Rules:\n"
            "- Return strict JSON object: {\"menu_items\": [...]} only.\n"
            "- Translate: name, description, ingredients, taste, similarDish1, similarDish2, recommendation_reason, allergens, preparation_method.\n"
            "- Keep recommendation labels exactly as-is (Most Recommended/Recommended/Not Recommended) and keep price, spiciness_level unchanged.\n"
            "- Do not add/remove/reorder rows.\n"
            "- Ensure each output row has non-empty name (or item).\n"
        )

    def _build_translation_repair_prompt(
        self,
        source_rows: List[Dict[str, Any]],
        previous_rows: List[Dict[str, Any]],
        target_language: str,
        validation_error: str,
    ) -> str:
        return (
            "Fix the previous translation output. Return strict JSON only.\n"
            f"Validation error to fix: {validation_error}\n"
            f"Target language: {target_language}\n\n"
            "Source rows (must be preserved count/order):\n"
            f"{json.dumps(source_rows, ensure_ascii=False)}\n\n"
            "Previous invalid output:\n"
            f"{json.dumps(previous_rows, ensure_ascii=False)}\n\n"
            "Output rules:\n"
            "- menu_items length must exactly equal source rows length.\n"
            "- Keep row order exactly unchanged.\n"
            "- Ensure each row has non-empty name (or item).\n"
            "- Do not alter price and spiciness_level semantic values.\n"
        )

    async def _call_groq_json(self, prompt: str, temperature: float = 0.0) -> Dict[str, Any]:
        payload = {
            "model": self.groq_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a strict JSON API. Return valid JSON only.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }

        url = f"{self.groq_api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json",
        }

        resp = await self._groq_client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        content = ((data.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
        parsed = self._extract_json(content)
        if not isinstance(parsed, dict):
            raise ValueError("Groq output must be a JSON object")
        return parsed

    async def _call_fallback_llm_json(self, prompt: str, temperature: float = 0.0) -> tuple[Dict[str, Any], str]:
        """Call OpenRouter → OpenAI → Anthropic as fallback enhancement providers.

        Returns (parsed_json, provider_name) on success, raises on total failure.
        """
        providers: list[tuple[str, str, str, str]] = []  # (name, url, key, model)

        if self.openrouter_api_key:
            providers.append((
                "openrouter",
                "https://openrouter.ai/api/v1/chat/completions",
                self.openrouter_api_key,
                "google/gemini-2.0-flash-001",  # fast + cheap on OpenRouter
            ))
        if self.openai_api_key:
            providers.append((
                "openai",
                "https://api.openai.com/v1/chat/completions",
                self.openai_api_key,
                "gpt-4o-mini",
            ))
        if self.anthropic_api_key:
            providers.append((
                "anthropic_via_openrouter",
                "https://openrouter.ai/api/v1/chat/completions",
                self.openrouter_api_key or "",
                "anthropic/claude-3-haiku",
            ))

        if not providers:
            raise RuntimeError("No fallback LLM API keys configured (OPENROUTER / OPENAI / ANTHROPIC)")

        last_exc: Optional[Exception] = None
        for name, url, key, model in providers:
            if not key:
                continue
            try:
                logger.info("Fallback LLM enhancement via %s model=%s", name, model)
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are a strict JSON API. Return valid JSON only."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": temperature,
                    "response_format": {"type": "json_object"},
                }
                headers = {
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                }
                resp = await self._fallback_client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                content = ((data.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
                parsed = self._extract_json(content)
                if not isinstance(parsed, dict):
                    raise ValueError(f"{name} output must be a JSON object")
                return parsed, name
            except Exception as exc:
                last_exc = exc
                logger.warning("Fallback LLM %s failed: %s", name, exc)

        raise last_exc or RuntimeError("All fallback LLM providers failed")

    async def _call_groq_llama_json(self, prompt: str, temperature: float = 0.0) -> Dict[str, Any]:
        """Call Groq with Llama 3.3 70B model (same API key, different model)."""
        payload = {
            "model": self.llama_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a strict JSON API. Return valid JSON only.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }

        url = f"{self.groq_api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json",
        }

        resp = await self._groq_client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        content = ((data.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
        parsed = self._extract_json(content)
        if not isinstance(parsed, dict):
            raise ValueError("Llama output must be a JSON object")
        return parsed

    def _row_has_gaps(self, row: Dict[str, Any]) -> bool:
        """Check if a row has weak/missing fields that Llama should fill."""
        ingredients = row.get("ingredients") if isinstance(row.get("ingredients"), list) else []
        real_ingredients = [i for i in ingredients if i and "inferred" not in str(i).lower()]
        if len(real_ingredients) < 3:
            return True
        if not str(row.get("description_ingredients") or "").strip():
            return True
        if not str(row.get("taste") or "").strip():
            return True
        if not str(row.get("similarDish1") or "").strip() or not str(row.get("similarDish2") or "").strip():
            return True
        if not row.get("allergens") or not isinstance(row.get("allergens"), list) or len(row.get("allergens", [])) == 0:
            return True
        if not str(row.get("spiciness_level") or "").strip() or str(row.get("spiciness_level") or "") == "none":
            return True
        if not str(row.get("preparation_method") or "").strip() or str(row.get("preparation_method") or "") == "other":
            return True
        return False

    def _build_llama_gapfill_prompt(self, rows: List[Dict[str, Any]], health_profile: Dict[str, Any]) -> str:
        """Build a prompt for Llama 3.3 70B to fill gaps in already-enhanced rows."""
        return (
            "You are an expert culinary database. You receive menu dishes that already have PARTIAL enrichment.\n"
            "Your job: review every field of every dish and REPLACE any weak, generic, or missing values with "
            "accurate, dish-specific culinary knowledge.\n\n"
            "Health profile:\n"
            f"{json.dumps(health_profile, ensure_ascii=False)}\n\n"
            "Current enriched rows (some fields may be empty, generic, or inaccurate):\n"
            f"{json.dumps(rows, ensure_ascii=False)}\n\n"
            "Return strict JSON: {\"menu_items\": [...]}\n\n"
            "For EVERY dish, ensure ALL of these fields are filled with REAL culinary knowledge:\n"
            "- \"item\": keep the dish name unchanged\n"
            "- \"description_ingredients\": a vivid 1-2 sentence description of what THIS specific dish actually is. "
            "If the current description is generic (e.g. 'a thoughtfully prepared dish'), REPLACE it with a real description.\n"
            "- \"price\": keep unchanged\n"
            "- \"ingredients\": list at least 5-8 REAL, specific ingredients for this dish as traditionally prepared. "
            "Include proteins, vegetables, sauces, spices, and base ingredients. Never use 'traditional ingredients inferred from dish name'.\n"
            "- \"taste\": the PRIMARY taste (spicy|salty|tangy|sweet|savory|umami|mild|mixed) — be dish-specific.\n"
            "- \"similarDish1\": a REAL well-known dish from ANOTHER cuisine with similar flavors.\n"
            "- \"similarDish2\": another REAL dish from a DIFFERENT cuisine.\n"
            "- \"recommendation\": keep unchanged if already set.\n"
            "- \"recommendation_reason\": keep unchanged if already set.\n"
            "- \"category\": keep unchanged.\n"
            "- \"allergens\": list REAL allergens based on actual ingredients (gluten, dairy, nuts, shellfish, eggs, soy, fish, peanuts, sesame). "
            "A pizza has [\"gluten\", \"dairy\"]. A pad thai has [\"peanuts\", \"soy\", \"eggs\"]. NEVER leave empty if there are real allergens.\n"
            "- \"spiciness_level\": rate accurately (none|mild|medium|hot|extra hot).\n"
            "- \"preparation_method\": identify the PRIMARY cooking method (grilled|fried|baked|steamed|raw|sautéed|roasted|boiled|other).\n\n"
            "RULES:\n"
            "- Output row count MUST equal input row count.\n"
            "- Preserve row order exactly.\n"
            "- Do NOT change item names or prices.\n"
            "- Do NOT change recommendation/recommendation_reason if already filled.\n"
            "- IMPROVE every other field where the current value is weak, empty, or generic.\n"
            "- If a field already has good data, keep it.\n"
        )

    async def gapfill_with_llama(
        self,
        enhanced_rows: List[Dict[str, Any]],
        health_profile: Optional[Dict[str, Any]] = None,
    ) -> tuple[List[Dict[str, Any]], bool]:
        """Run Llama 3.3 70B on Groq to fill gaps in enhanced rows.

        Only sends rows that actually have gaps to save tokens (Llama 3.3 has
        a tight 100K TPD free-tier limit on Groq).

        Returns (improved_rows, success_flag).
        On failure, returns the original rows unchanged with success=False.
        """
        if not self.groq_api_key:
            return enhanced_rows, False

        # Identify which rows need gap-filling
        gap_indices = [i for i, row in enumerate(enhanced_rows) if self._row_has_gaps(row)]
        if not gap_indices:
            logger.info("Llama gap-fill: all %s rows already complete, skipping", len(enhanced_rows))
            return enhanced_rows, False

        # Only send rows with gaps to save tokens
        gap_rows = [enhanced_rows[i] for i in gap_indices]

        logger.info(
            "Llama gap-fill: %s/%s rows have gaps, sending only those to %s",
            len(gap_rows), len(enhanced_rows), self.llama_model,
        )

        health_profile = health_profile or {}
        prompt = self._build_llama_gapfill_prompt(gap_rows, health_profile)

        try:
            parsed = await self._call_groq_llama_json(prompt=prompt, temperature=0.0)
            rows = parsed.get("menu_items") if isinstance(parsed.get("menu_items"), list) else []

            if len(rows) != len(gap_rows):
                logger.warning(
                    "Llama gap-fill row count mismatch: expected=%s got=%s, discarding",
                    len(gap_rows), len(rows),
                )
                return enhanced_rows, False

            # Merge Llama results back into the full list
            result = list(enhanced_rows)  # shallow copy
            for slot, llama_row in zip(gap_indices, rows):
                orig = enhanced_rows[slot]
                m = dict(orig)

                # item and price: never change
                m["item"] = orig.get("item")
                m["price"] = orig.get("price")

                # description: upgrade if original was generic
                orig_desc = str(orig.get("description_ingredients") or "").strip()
                llama_desc = str(llama_row.get("description_ingredients") or "").strip()
                if llama_desc and (
                    not orig_desc
                    or "thoughtfully prepared" in orig_desc.lower()
                    or "quality ingredients" in orig_desc.lower()
                    or len(orig_desc) < 20
                ):
                    m["description_ingredients"] = llama_desc

                # ingredients: upgrade if original had < 3 real ingredients
                orig_ing = orig.get("ingredients") if isinstance(orig.get("ingredients"), list) else []
                llama_ing = llama_row.get("ingredients") if isinstance(llama_row.get("ingredients"), list) else []
                real_orig = [i for i in orig_ing if i and "inferred" not in str(i).lower()]
                if len(real_orig) < 3 and len(llama_ing) >= 3:
                    m["ingredients"] = llama_ing

                # taste: upgrade if missing
                if not str(orig.get("taste") or "").strip() and str(llama_row.get("taste") or "").strip():
                    m["taste"] = llama_row["taste"]

                # similarDish1/2: upgrade if missing
                if not str(orig.get("similarDish1") or "").strip() and str(llama_row.get("similarDish1") or "").strip():
                    m["similarDish1"] = llama_row["similarDish1"]
                if not str(orig.get("similarDish2") or "").strip() and str(llama_row.get("similarDish2") or "").strip():
                    m["similarDish2"] = llama_row["similarDish2"]

                # allergens: upgrade if empty
                orig_allergens = orig.get("allergens") if isinstance(orig.get("allergens"), list) else []
                llama_allergens = llama_row.get("allergens") if isinstance(llama_row.get("allergens"), list) else []
                if not orig_allergens and llama_allergens:
                    m["allergens"] = llama_allergens

                # spiciness_level: upgrade if missing/generic
                orig_spice = str(orig.get("spiciness_level") or "").strip()
                llama_spice = str(llama_row.get("spiciness_level") or "").strip()
                if (not orig_spice or orig_spice == "none") and llama_spice:
                    m["spiciness_level"] = llama_spice

                # preparation_method: upgrade if missing/generic
                orig_prep = str(orig.get("preparation_method") or "").strip()
                llama_prep = str(llama_row.get("preparation_method") or "").strip()
                if (not orig_prep or orig_prep == "other") and llama_prep:
                    m["preparation_method"] = llama_prep

                # recommendation: never change from Qwen3 output
                # category: never change

                result[slot] = m

            logger.info("Llama gap-fill completed successfully (%s rows improved)", len(gap_indices))
            return result, True

        except Exception as exc:
            logger.warning("Llama gap-fill failed, keeping original rows: %s", exc)
            return enhanced_rows, False

    def _validate_enhancement_rows(self, source_rows: List[Dict[str, Any]], rows: List[Dict[str, Any]]) -> tuple[bool, str]:
        if len(rows) != len(source_rows):
            return False, f"row_count_mismatch expected={len(source_rows)} actual={len(rows)}"

        for idx, row in enumerate(rows):
            item_text = str(row.get("item") or "").strip()
            if not item_text:
                return False, f"missing_item_at_index={idx}"
            if _PRICE_TOKEN_RE.search(item_text):
                return False, f"item_contains_price_token_at_index={idx}"

        return True, "ok"

    def _validate_translation_rows(self, source_rows: List[Dict[str, Any]], rows: List[Dict[str, Any]]) -> tuple[bool, str]:
        if len(rows) != len(source_rows):
            return False, f"row_count_mismatch expected={len(source_rows)} actual={len(rows)}"

        for idx, row in enumerate(rows):
            name_text = str(row.get("name") or row.get("item") or "").strip()
            if not name_text:
                return False, f"missing_name_at_index={idx}"

        return True, "ok"

    def _sanitize_qwen_rows(self, rows: List[Dict[str, Any]], base_rows: List[Dict[str, Any]], health_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        menu_names = {self._norm_name(row.get("item")) for row in base_rows if self._norm_name(row.get("item"))}
        has_health_context = bool(
            (health_profile.get("health_conditions") or [])
            or (health_profile.get("allergies") or [])
            or (health_profile.get("dietary_preferences") or [])
        )

        sanitized: List[Dict[str, Any]] = []
        for row in rows:
            item_name = row.get("item")
            item_name, row_price = self._split_price_from_item(item_name, row.get("price"))
            item_key = self._norm_name(item_name)
            description = self._strip_price_token(row.get("description_ingredients"))

            similar_1 = row.get("similarDish1")
            similar_2 = row.get("similarDish2")
            if self._norm_name(similar_1) in menu_names or self._norm_name(similar_1) == item_key:
                similar_1 = None
            if self._norm_name(similar_2) in menu_names or self._norm_name(similar_2) == item_key:
                similar_2 = None

            recommendation = row.get("recommendation")
            recommendation_reason = row.get("recommendation_reason")
            if not has_health_context:
                recommendation = None
                recommendation_reason = None

            sanitized.append(
                {
                    "item": item_name,
                    "description_ingredients": description,
                    "price": row_price,
                    "category": row.get("category"),
                    "ingredients": row.get("ingredients") if isinstance(row.get("ingredients"), list) else [],
                    "taste": row.get("taste"),
                    "similarDish1": similar_1,
                    "similarDish2": similar_2,
                    "recommendation": recommendation,
                    "recommendation_reason": recommendation_reason,
                    "allergens": row.get("allergens") if isinstance(row.get("allergens"), list) else [],
                    "spiciness_level": row.get("spiciness_level"),
                    "preparation_method": row.get("preparation_method"),
                }
            )

        return sanitized

    def _normalize_enhanced_rows(self, source_rows: List[Dict[str, Any]], rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        rows_by_name: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            key = self._norm_name(row.get("item"))
            if key and key not in rows_by_name:
                rows_by_name[key] = row

        for index, source in enumerate(source_rows):
            candidate = rows[index] if index < len(rows) else {}
            source_name = source.get("item")
            source_key = self._norm_name(source_name)
            candidate_key = self._norm_name(candidate.get("item"))
            if source_key and candidate_key and source_key != candidate_key:
                candidate = rows_by_name.get(source_key, candidate)

            item_name, row_price = self._split_price_from_item(
                candidate.get("item") or source_name,
                candidate.get("price") if candidate.get("price") is not None else source.get("price"),
            )

            normalized.append(
                {
                    "item": item_name,
                    "description_ingredients": self._strip_price_token(
                        candidate.get("description_ingredients")
                        if candidate.get("description_ingredients") is not None
                        else source.get("description_ingredients")
                    ),
                    "price": row_price,
                    "category": candidate.get("category") if candidate.get("category") is not None else source.get("category"),
                    "ingredients": candidate.get("ingredients") if isinstance(candidate.get("ingredients"), list) else [],
                    "taste": candidate.get("taste"),
                    "similarDish1": candidate.get("similarDish1"),
                    "similarDish2": candidate.get("similarDish2"),
                    "recommendation": candidate.get("recommendation"),
                    "recommendation_reason": candidate.get("recommendation_reason"),
                    "allergens": candidate.get("allergens") if isinstance(candidate.get("allergens"), list) else [],
                    "spiciness_level": candidate.get("spiciness_level"),
                    "preparation_method": candidate.get("preparation_method"),
                }
            )

        return normalized

    def _infer_ingredients(self, item_name: str, description: str) -> List[str]:
        source = f"{item_name} {description}".lower()
        keyword_to_ingredient = {
            "pizza": ["dough", "tomato", "cheese"],
            "pasta": ["durum wheat pasta", "olive oil", "salt"],
            "burger": ["bun", "patty", "lettuce"],
            "salad": ["greens", "olive oil", "seasoning"],
            "soup": ["broth", "onion", "herbs"],
            "curry": ["onion", "spices", "oil"],
            "taco": ["tortilla", "protein", "salsa"],
            "noodle": ["noodles", "oil", "seasoning"],
            "risotto": ["arborio rice", "broth", "parmesan"],
            "steak": ["beef", "salt", "pepper"],
            "fish": ["fish", "lemon", "herbs"],
            "chicken": ["chicken", "garlic", "spices"],
            "dessert": ["sugar", "flour", "butter"],
            "cake": ["flour", "sugar", "eggs"],
            "ice cream": ["milk", "sugar", "cream"],
        }
        for key, ingredients in keyword_to_ingredient.items():
            if key in source:
                return ingredients
        return ["traditional ingredients inferred from dish name"]

    def _infer_taste(self, item_name: str, description: str) -> str:
        source = f"{item_name} {description}".lower()
        if any(token in source for token in ["chili", "spicy", "pepper", "hot"]):
            return "spicy"
        if any(token in source for token in ["dessert", "cake", "sweet", "honey", "sugar"]):
            return "sweet"
        if any(token in source for token in ["lemon", "vinegar", "pickled", "citrus"]):
            return "tangy"
        if any(token in source for token in ["soup", "broth", "meat", "cheese", "umami"]):
            return "savory"
        return "savory"

    def _infer_spiciness(self, item_name: str, description: str) -> str:
        source = f"{item_name} {description}".lower()
        if any(token in source for token in ["extra hot", "very spicy"]):
            return "extra hot"
        if any(token in source for token in ["hot", "chili", "spicy"]):
            return "medium"
        if any(token in source for token in ["pepper", "masala", "salsa"]):
            return "mild"
        return "none"

    def _infer_preparation_method(self, item_name: str, description: str) -> str:
        source = f"{item_name} {description}".lower()
        if "grill" in source:
            return "grilled"
        if "fried" in source:
            return "fried"
        if "baked" in source:
            return "baked"
        if "steam" in source:
            return "steamed"
        if "roast" in source:
            return "roasted"
        if "boil" in source:
            return "boiled"
        if "raw" in source:
            return "raw"
        if "saute" in source or "sauté" in source:
            return "sautéed"
        return "other"

    def _infer_description(self, item_name: str) -> str:
        source = item_name.lower()
        if "margherita" in source:
            return "Classic Italian pizza with tomato sauce, fresh mozzarella, and fragrant basil on a thin crispy crust."
        if "pizza" in source:
            return f"{item_name} – oven-baked pizza topped with signature ingredients on a golden, crispy crust."
        if "carbonara" in source:
            return "Traditional Roman pasta with eggs, Pecorino Romano, crispy guanciale, and freshly cracked black pepper."
        if "tiramisu" in source:
            return "Italian dessert of espresso-soaked ladyfingers layered with mascarpone cream, dusted with rich cocoa powder."
        if any(t in source for t in ["spaghetti", "pasta", "penne", "fettuccine", "linguine", "tagliatelle"]):
            return f"{item_name} – Italian pasta prepared with a carefully crafted sauce and house-seasoned garnishes."
        if "lasagna" in source or "lasagne" in source:
            return "Hearty layered Italian pasta baked with meat sauce, creamy béchamel, and melted mozzarella."
        if "risotto" in source:
            return "Creamy Italian Arborio rice slowly cooked with broth, white wine, and finished with Parmesan."
        if "burger" in source:
            return f"Juicy {item_name} in a toasted brioche bun with crisp lettuce, tomato, and house-made sauce."
        if any(t in source for t in ["sandwich", "sub", "wrap"]):
            return f"Freshly made {item_name} packed with premium fillings and house dressing."
        if any(t in source for t in ["salad", "caesar", "niçoise"]):
            return f"Crisp {item_name} with seasonal greens, fresh toppings, and a light house vinaigrette."
        if any(t in source for t in ["curry", "masala", "tikka", "korma"]):
            return f"Aromatic {item_name} simmered in a fragrant blend of spices with tender protein."
        if "biryani" in source:
            return "Fragrant basmati rice slow-cooked with marinated protein, caramelised onions, and saffron."
        if any(t in source for t in ["ramen", "pho", "noodle"]):
            return f"Steaming bowl of {item_name} with rich broth, springy noodles, and traditional garnishes."
        if any(t in source for t in ["soup", "bisque", "chowder"]):
            return f"Warming {item_name} simmered from scratch with fresh vegetables and aromatic herbs."
        if any(t in source for t in ["sushi", "roll", "maki", "nigiri"]):
            return f"Artfully crafted {item_name} with seasoned sushi rice and premium, fresh fillings."
        if any(t in source for t in ["taco", "burrito", "quesadilla", "enchilada"]):
            return f"{item_name} – Mexican-inspired dish wrapped with seasoned filling, salsa, and fresh herbs."
        if "steak" in source or any(t in source for t in ["ribeye", "tenderloin", "sirloin"]):
            return f"Premium {item_name} dry-aged and grilled to your preferred doneness, served with seasonal sides."
        if any(t in source for t in ["chicken", "poultry", "wings"]):
            return f"Tender {item_name} seasoned with herbs and spices, cooked to golden perfection."
        if any(t in source for t in ["salmon", "tuna", "fish", "seafood", "shrimp", "prawn", "lobster"]):
            return f"Fresh {item_name} prepared to highlight its natural flavour, served with a citrus garnish."
        if any(t in source for t in ["cake", "cheesecake", "tart"]):
            return f"Indulgent {item_name} baked fresh daily with premium ingredients and house-made frosting."
        if any(t in source for t in ["ice cream", "gelato", "sorbet", "sundae"]):
            return f"Creamy {item_name} made from the finest dairy and natural flavors, served chilled."
        if any(t in source for t in ["brownie", "waffle", "pancake", "crepe"]):
            return f"House-made {item_name} served warm with seasonal accompaniments."
        return f"{item_name} – a thoughtfully prepared dish made with quality ingredients and house seasoning."

    def _infer_similar_dishes(self, item_name: str, description: str) -> tuple[str, str]:
        source = f"{item_name} {description}".lower()
        if any(token in source for token in ["pizza", "flatbread"]):
            return ("Lahmacun", "Manakish")
        if any(token in source for token in ["pasta", "noodle"]):
            return ("Dan Dan Noodles", "Yakisoba")
        if any(token in source for token in ["curry", "masala"]):
            return ("Thai Green Curry", "Japanese Katsu Curry")
        if any(token in source for token in ["burger", "sandwich"]):
            return ("Arepa Reina Pepiada", "Banh Mi")
        if any(token in source for token in ["soup", "broth"]):
            return ("Tom Yum", "Miso Soup")
        if any(token in source for token in ["dessert", "cake", "sweet"]):
            return ("Baklava", "Mochi")
        return ("Paella", "Bibimbap")

    def _fill_required_enhanced_fields(
        self,
        base_row: Dict[str, Any],
        row: Dict[str, Any],
        has_health_context: bool,
    ) -> Dict[str, Any]:
        name = str(row.get("item") or base_row.get("item") or "Unknown").strip() or "Unknown"
        description = (
            row.get("description_ingredients")
            if row.get("description_ingredients") not in (None, "")
            else base_row.get("description_ingredients")
        )
        description = str(description).strip() if description not in (None, "") else self._infer_description(name)

        ingredients = row.get("ingredients") if isinstance(row.get("ingredients"), list) else []
        ingredients = [str(value).strip() for value in ingredients if str(value or "").strip()]
        if not ingredients:
            ingredients = self._infer_ingredients(name, description)

        similar_1 = str(row.get("similarDish1") or "").strip()
        similar_2 = str(row.get("similarDish2") or "").strip()
        if not similar_1 or not similar_2:
            inferred_1, inferred_2 = self._infer_similar_dishes(name, description)
            similar_1 = similar_1 or inferred_1
            similar_2 = similar_2 or inferred_2
        if self._norm_name(similar_1) == self._norm_name(name):
            similar_1 = "Paella"
        if self._norm_name(similar_2) in {self._norm_name(name), self._norm_name(similar_1)}:
            similar_2 = "Bibimbap"

        recommendation = row.get("recommendation")
        recommendation_reason = row.get("recommendation_reason")
        if recommendation not in {"Most Recommended", "Recommended", "Not Recommended"}:
            recommendation = "Recommended"
        if not recommendation_reason:
            recommendation_reason = (
                "Aligned with your saved health profile."
                if has_health_context
                else "General recommendation without profile-specific constraints."
            )

        allergens = row.get("allergens") if isinstance(row.get("allergens"), list) else []
        allergens = [str(value).strip() for value in allergens if str(value or "").strip()]
        allergens = [a for a in allergens if a.lower() != "unknown"]

        taste = str(row.get("taste") or "").strip() or self._infer_taste(name, description)
        spiciness = str(row.get("spiciness_level") or "").strip() or self._infer_spiciness(name, description)
        prep_method = str(row.get("preparation_method") or "").strip() or self._infer_preparation_method(name, description)
        category = str(row.get("category") or base_row.get("category") or "other").strip() or "other"

        return {
            "item": name,
            "description_ingredients": description,
            "price": row.get("price") if row.get("price") is not None else base_row.get("price"),
            "category": category,
            "ingredients": ingredients,
            "taste": taste,
            "similarDish1": similar_1,
            "similarDish2": similar_2,
            "recommendation": recommendation,
            "recommendation_reason": recommendation_reason,
            "allergens": allergens,
            "spiciness_level": spiciness,
            "preparation_method": prep_method,
        }

    def _split_price_from_item(self, item_value: Any, price_value: Any) -> tuple[str, Any]:
        item_text = str(item_value or "").strip()
        existing_price = price_value
        if not item_text:
            return "", existing_price

        match = _PRICE_TOKEN_RE.search(item_text)
        if not match:
            return item_text, existing_price

        inferred_price = match.group("price").strip()
        cleaned_item = (item_text[: match.start()] + " " + item_text[match.end() :]).strip(" -–—|\t")
        cleaned_item = re.sub(r"\s{2,}", " ", cleaned_item).strip()

        final_price = existing_price if existing_price not in (None, "", "-") else inferred_price
        return cleaned_item or item_text, final_price

    def _strip_price_token(self, value: Any) -> Any:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return text
        stripped = _PRICE_TOKEN_RE.sub("", text)
        stripped = re.sub(r"\s{2,}", " ", stripped).strip(" -–—|\t")
        return stripped or text

    def _normalize_extracted_rows(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        seen = set()
        for row in rows:
            item, price = self._split_price_from_item(row.get("item"), row.get("price"))
            description = self._strip_price_token(row.get("description_ingredients"))
            identity = self._row_identity({"item": item, "price": price, "category": row.get("category")})
            if not identity[0] or identity in seen:
                continue
            seen.add(identity)
            normalized.append(
                {
                    "item": item,
                    "description_ingredients": description,
                    "price": price,
                    "currency": row.get("currency"),
                    "category": row.get("category"),
                }
            )
        return normalized

    def _row_display_name(self, row: Dict[str, Any]) -> str:
        return str(row.get("name") or row.get("item") or "").strip()

    def _normalize_translated_rows(
        self,
        source_rows: List[Dict[str, Any]],
        translated_rows: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if not source_rows:
            return []

        translated_by_name: Dict[str, Dict[str, Any]] = {}
        for row in translated_rows:
            key = self._norm_name(self._row_display_name(row))
            if key:
                translated_by_name[key] = row

        normalized: List[Dict[str, Any]] = []
        for index, source in enumerate(source_rows):
            source_name = self._row_display_name(source)
            key = self._norm_name(source_name)
            translated = translated_by_name.get(key)
            if translated is None and index < len(translated_rows):
                translated = translated_rows[index]
            translated = translated or {}

            normalized.append(
                {
                    "name": translated.get("name") or translated.get("item") or source.get("name") or source.get("item") or "Unknown",
                    "price": translated.get("price") if translated.get("price") is not None else source.get("price"),
                    "description": translated.get("description") if translated.get("description") is not None else source.get("description"),
                    "category": translated.get("category") if translated.get("category") is not None else source.get("category"),
                    "ingredients": translated.get("ingredients") if isinstance(translated.get("ingredients"), list) else (source.get("ingredients") if isinstance(source.get("ingredients"), list) else []),
                    "taste": translated.get("taste") if translated.get("taste") is not None else source.get("taste"),
                    "similarDish1": translated.get("similarDish1") if translated.get("similarDish1") is not None else source.get("similarDish1"),
                    "similarDish2": translated.get("similarDish2") if translated.get("similarDish2") is not None else source.get("similarDish2"),
                    "recommendation": source.get("recommendation"),
                    "recommendation_reason": translated.get("recommendation_reason") if translated.get("recommendation_reason") is not None else source.get("recommendation_reason"),
                    "allergens": translated.get("allergens") if isinstance(translated.get("allergens"), list) else (source.get("allergens") if isinstance(source.get("allergens"), list) else []),
                    "spiciness_level": translated.get("spiciness_level") if translated.get("spiciness_level") is not None else source.get("spiciness_level"),
                    "preparation_method": translated.get("preparation_method") if translated.get("preparation_method") is not None else source.get("preparation_method"),
                }
            )

        return normalized

    async def translate_menu_items(self, menu_items: List[Dict[str, Any]], target_language: str) -> List[Dict[str, Any]]:
        if not target_language or target_language.lower() in {"en", "english", "auto"}:
            return menu_items

        if not self.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")

        prompt = self._build_translation_prompt(menu_items, target_language)
        previous_rows: List[Dict[str, Any]] = []
        last_error = "unknown"

        for attempt in range(1, _MAX_STRUCTURED_RETRIES + 1):
            try:
                parsed = await self._call_groq_json(prompt=prompt, temperature=0.0)
                translated = parsed.get("menu_items") if isinstance(parsed.get("menu_items"), list) else []
                is_valid, validation_error = self._validate_translation_rows(menu_items, translated)
                if is_valid:
                    return self._normalize_translated_rows(menu_items, translated)

                last_error = validation_error
                previous_rows = translated
                prompt = self._build_translation_repair_prompt(
                    source_rows=menu_items,
                    previous_rows=previous_rows,
                    target_language=target_language,
                    validation_error=validation_error,
                )
                logger.warning(
                    "Groq translation validation failed attempt=%s/%s reason=%s",
                    attempt,
                    _MAX_STRUCTURED_RETRIES,
                    validation_error,
                )
            except Exception as exc:
                last_error = str(exc)
                prompt = self._build_translation_repair_prompt(
                    source_rows=menu_items,
                    previous_rows=previous_rows,
                    target_language=target_language,
                    validation_error=last_error,
                )
                logger.warning(
                    "Groq translation attempt failed attempt=%s/%s error=%s",
                    attempt,
                    _MAX_STRUCTURED_RETRIES,
                    exc,
                )

        logger.warning("Groq translation failed after retries, returning source rows: %s", last_error)
        return menu_items

    async def extract_with_gemini(self, image_bytes: bytes, language_hint: str = "auto") -> Dict[str, Any]:
        if not self.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")

        prompt = self._build_gemini_prompt(language_hint)
        first_pass = await self._call_gemini(prompt=prompt, image_bytes=image_bytes)
        first_rows = self._normalize_extracted_rows(first_pass.get("menu_items") or [])

        existing_names = [str(row.get("item") or "") for row in first_rows if str(row.get("item") or "").strip()]
        second_prompt = self._build_gemini_second_pass_prompt(language_hint, existing_names)

        try:
            second_pass = await self._call_gemini(prompt=second_prompt, image_bytes=image_bytes)
            second_rows = self._normalize_extracted_rows(second_pass.get("menu_items") or [])
            merged_rows = self._normalize_extracted_rows(self._merge_unique_rows(first_rows, second_rows))
            return {
                "menu_items": merged_rows or first_rows,
                "raw_text": second_pass.get("raw_text", "") or first_pass.get("raw_text", ""),
            }
        except Exception as exc:
            logger.warning("Gemini second-pass extraction failed, using first-pass rows: %s", exc)

        return {"menu_items": first_rows, "raw_text": first_pass.get("raw_text", "")}

    async def enhance_with_groq(
        self,
        extracted_rows: List[Dict[str, Any]],
        health_profile: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")

        health_profile = health_profile or {
            "health_conditions": [],
            "allergies": [],
            "dietary_preferences": [],
            "medical_notes": None,
        }

        prompt = self._build_groq_prompt(extracted_rows, health_profile)
        previous_rows: List[Dict[str, Any]] = []
        last_error = "unknown"

        logger.info("Groq enhancement request model=%s items=%s", self.groq_model, len(extracted_rows))

        for attempt in range(1, _MAX_STRUCTURED_RETRIES + 1):
            try:
                parsed = await self._call_groq_json(prompt=prompt, temperature=0.0)
                rows = parsed.get("menu_items") if isinstance(parsed.get("menu_items"), list) else []
                is_valid, validation_error = self._validate_enhancement_rows(extracted_rows, rows)
                if is_valid:
                    return {
                        "menu_items": rows,
                        "metadata": {
                            "enhancement_attempts": attempt,
                            "enhancement_validated": True,
                            "enhancement_provider": "groq",
                        },
                    }

                last_error = validation_error
                previous_rows = rows
                prompt = self._build_groq_repair_prompt(
                    extracted_rows=extracted_rows,
                    health_profile=health_profile,
                    previous_rows=previous_rows,
                    validation_error=validation_error,
                )
                logger.warning(
                    "Groq enhancement validation failed attempt=%s/%s reason=%s",
                    attempt,
                    _MAX_STRUCTURED_RETRIES,
                    validation_error,
                )
            except Exception as exc:
                last_error = str(exc)
                prompt = self._build_groq_repair_prompt(
                    extracted_rows=extracted_rows,
                    health_profile=health_profile,
                    previous_rows=previous_rows,
                    validation_error=last_error,
                )
                logger.warning(
                    "Groq enhancement attempt failed attempt=%s/%s error=%s",
                    attempt,
                    _MAX_STRUCTURED_RETRIES,
                    exc,
                )

        # ------- FALLBACK: try OpenRouter / OpenAI / Anthropic -------
        logger.warning("Groq exhausted %s retries (%s), trying fallback LLM providers", _MAX_STRUCTURED_RETRIES, last_error)
        fallback_prompt = self._build_groq_prompt(extracted_rows, health_profile)
        try:
            parsed, provider = await self._call_fallback_llm_json(prompt=fallback_prompt, temperature=0.0)
            rows = parsed.get("menu_items") if isinstance(parsed.get("menu_items"), list) else []
            is_valid, validation_error = self._validate_enhancement_rows(extracted_rows, rows)
            if is_valid:
                logger.info("Fallback LLM enhancement succeeded via %s", provider)
                return {
                    "menu_items": rows,
                    "metadata": {
                        "enhancement_attempts": _MAX_STRUCTURED_RETRIES + 1,
                        "enhancement_validated": True,
                        "enhancement_provider": provider,
                    },
                }
            logger.warning("Fallback LLM %s returned invalid rows: %s", provider, validation_error)
        except Exception as fallback_exc:
            logger.warning("All fallback LLM providers also failed: %s", fallback_exc)

        raise ValueError(f"Enhancement failed after Groq retries + fallback providers: {last_error}")

    async def process_menu(
        self,
        image_bytes: bytes,
        language_hint: str = "auto",
        health_profile: Optional[Dict[str, Any]] = None,
        use_groq_enhancement: bool = True,
    ) -> Dict[str, Any]:
        extracted = await self.extract_with_gemini(image_bytes=image_bytes, language_hint=language_hint)
        base_rows = extracted.get("menu_items", [])
        health_context = bool(
            (health_profile or {}).get("health_conditions")
            or (health_profile or {}).get("allergies")
            or (health_profile or {}).get("dietary_preferences")
        )

        if not use_groq_enhancement:
            gemini_rows = [
                {
                    "name": row.get("item") or "Unknown",
                    "price": row.get("price"),
                    "description": row.get("description_ingredients"),
                    "category": row.get("category"),
                    "ingredients": [],
                    "taste": None,
                    "similarDish1": None,
                    "similarDish2": None,
                    "recommendation": None,
                    "recommendation_reason": None,
                    "allergens": [],
                    "spiciness_level": None,
                    "preparation_method": None,
                }
                for row in base_rows
            ]
            return {
                "menu_items": gemini_rows,
                "gemini_menu_items": gemini_rows,
                "qwen_menu_items": gemini_rows,
                "raw_text": extracted.get("raw_text", ""),
                "metadata": {
                    "ocr_model": self.gemini_model,
                    "enhancement_model": None,
                    "pipeline": "gemini_only",
                },
            }

        try:
            enhanced = await self.enhance_with_groq(extracted_rows=base_rows, health_profile=health_profile)
        except Exception as exc:
            logger.warning("Groq enhancement failed, returning Gemini-only rows: %s", exc)
            gemini_rows = [
                {
                    "name": row.get("item") or "Unknown",
                    "price": row.get("price"),
                    "description": row.get("description_ingredients"),
                    "category": row.get("category"),
                    "ingredients": [],
                    "taste": None,
                    "similarDish1": None,
                    "similarDish2": None,
                    "recommendation": None,
                    "recommendation_reason": None,
                    "allergens": [],
                    "spiciness_level": None,
                    "preparation_method": None,
                }
                for row in base_rows
            ]
            return {
                "menu_items": gemini_rows,
                "gemini_menu_items": gemini_rows,
                "qwen_menu_items": gemini_rows,
                "raw_text": extracted.get("raw_text", ""),
                "metadata": {
                    "ocr_model": self.gemini_model,
                    "enhancement_model": self.groq_model,
                    "pipeline": "gemini_only",
                    "enhancement_error": str(exc),
                },
            }

        enhanced_rows = enhanced.get("menu_items", [])
        enhancement_meta = enhanced.get("metadata") if isinstance(enhanced.get("metadata"), dict) else {}
        enhanced_rows = self._sanitize_qwen_rows(enhanced_rows, base_rows, health_profile or {})
        enhanced_rows = self._normalize_enhanced_rows(base_rows, enhanced_rows)
        enhanced_rows = [
            self._fill_required_enhanced_fields(base_row, row, health_context)
            for base_row, row in zip(base_rows, enhanced_rows)
        ]

        # ---- Step 3: Llama 3.3 70B gap-fill pass ----
        enhanced_rows, llama_used = await self.gapfill_with_llama(
            enhanced_rows=enhanced_rows, health_profile=health_profile,
        )

        final_rows: List[Dict[str, Any]] = []
        for row in enhanced_rows:
            final_rows.append(
                {
                    "name": row.get("item") or "Unknown",
                    "price": row.get("price"),
                    "description": row.get("description_ingredients"),
                    "category": row.get("category"),
                    "ingredients": row.get("ingredients") if isinstance(row.get("ingredients"), list) else [],
                    "taste": row.get("taste"),
                    "similarDish1": row.get("similarDish1"),
                    "similarDish2": row.get("similarDish2"),
                    "recommendation": row.get("recommendation"),
                    "recommendation_reason": row.get("recommendation_reason"),
                    "allergens": row.get("allergens") if isinstance(row.get("allergens"), list) else [],
                    "spiciness_level": row.get("spiciness_level"),
                    "preparation_method": row.get("preparation_method"),
                }
            )

        if not final_rows:
            final_rows = [
                {
                    "name": row.get("item") or "Unknown",
                    "price": row.get("price"),
                    "description": row.get("description_ingredients"),
                    "category": row.get("category"),
                    "ingredients": [],
                    "taste": None,
                    "similarDish1": None,
                    "similarDish2": None,
                    "recommendation": None,
                    "recommendation_reason": None,
                    "allergens": [],
                    "spiciness_level": None,
                    "preparation_method": None,
                }
                for row in base_rows
            ]

        gemini_rows = [
            {
                "name": row.get("item") or "Unknown",
                "price": row.get("price"),
                "description": row.get("description_ingredients"),
                "category": row.get("category"),
                "ingredients": [],
                "taste": None,
                "similarDish1": None,
                "similarDish2": None,
                "recommendation": None,
                "recommendation_reason": None,
            }
            for row in base_rows
        ]

        return {
            "menu_items": final_rows,
            "gemini_menu_items": gemini_rows,
            "qwen_menu_items": final_rows,
            "raw_text": extracted.get("raw_text", ""),
            "metadata": {
                "ocr_model": self.gemini_model,
                "enhancement_model": self.groq_model,
                "pipeline": "gemini_plus_groq",
                "ui_source": "qwen",
                "enhancement_provider": enhancement_meta.get("enhancement_provider", "groq"),
                "enhancement_attempts": enhancement_meta.get("enhancement_attempts", 1),
                "enhancement_validated": enhancement_meta.get("enhancement_validated", False),
                "llama_gapfill_model": self.llama_model if llama_used else None,
                "llama_gapfill_applied": llama_used,
            },
        }
