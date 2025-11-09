"""
Enhanced Qwen Table Extractor with Ingredient Matching
Integrates OCR text processing with Supabase ingredient database
"""

import os
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from openai import OpenAI
from anthropic import Anthropic
import logging
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class EnhancedQwenExtractor:
    """
    Enhanced Qwen extractor that processes OCR text and matches ingredients
    against Supabase database for comprehensive menu analysis
    """

    def __init__(self):
        # LLM clients
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.fallback_enabled = os.getenv("FALLBACK_ENABLED", "true").lower() == "true"

        # Supabase client for ingredient matching
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        if supabase_url and supabase_key:
            self.supabase: Client = create_client(supabase_url, supabase_key)
        else:
            self.supabase = None
            logger.warning("Supabase credentials not found - ingredient matching disabled")

    def process_menu_ocr(self, ocr_text: str, language: str = "en") -> Dict[str, Any]:
        """
        Complete pipeline: OCR -> Qwen extraction -> Ingredient matching -> Mobile delivery
        """
        try:
            logger.info(f"Processing OCR text with {len(ocr_text)} characters")

            # Step 1: Extract structured menu data using Qwen
            menu_data = self._extract_menu_with_qwen(ocr_text, language)

            if not menu_data.get("menu_items"):
                logger.warning("No menu items extracted from OCR")
                return self._create_empty_response()

            # Step 2: Enrich with ingredient database matching
            enriched_data = self._enrich_with_ingredients(menu_data)

            # Step 3: Add metadata for mobile app optimization
            final_data = self._optimize_for_mobile_delivery(enriched_data)

            logger.info(f"Successfully processed menu with {len(final_data.get('menu_items', []))} items")
            return final_data

        except Exception as e:
            logger.error(f"Failed to process menu OCR: {e}")
            return self._create_error_response(str(e))

    def _extract_menu_with_qwen(self, ocr_text: str, language: str) -> Dict[str, Any]:
        """Extract menu data using Qwen/OpenAI with detailed ingredient analysis"""
        try:
            prompt = self._build_menu_extraction_prompt(ocr_text, language)

            # Try OpenAI first
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert menu analyst. Extract detailed menu information with comprehensive ingredient analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )

            content = response.choices[0].message.content
            if content:
                return self._parse_menu_json(content)

        except Exception as e:
            logger.warning(f"OpenAI extraction failed: {e}")

        # Fallback to Anthropic if enabled
        if self.fallback_enabled:
            try:
                response = self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=4000,
                    temperature=0.1,
                    system="You are an expert menu analyst. Extract detailed menu information with comprehensive ingredient analysis.",
                    messages=[{"role": "user", "content": prompt}]
                )

                content = response.content[0].text
                if content:
                    return self._parse_menu_json(content)

            except Exception as e:
                logger.error(f"Anthropic extraction also failed: {e}")

        return self._create_fallback_menu_data(ocr_text)

    def _build_menu_extraction_prompt(self, ocr_text: str, language: str) -> str:
        """Build comprehensive menu extraction prompt"""
        return f"""
Analyze this restaurant menu OCR text and extract comprehensive information.

OCR TEXT:
{ocr_text}

INSTRUCTIONS:
1. Extract ALL menu items with complete details
2. Identify every ingredient mentioned for each dish
3. Include preparation methods, cooking techniques
4. Note allergens and dietary restrictions
5. Extract prices, descriptions, categories
6. Identify restaurant information

Return JSON in this exact format:
{{
    "restaurant_info": {{
        "name": "Restaurant Name",
        "cuisine_type": "Italian|Mediterranean|etc",
        "location": "City, Country",
        "price_range": "$|$$|$$$|$$$$",
        "specialties": ["signature dishes"]
    }},
    "menu_items": [
        {{
            "name": "Exact Dish Name",
            "price": 24.99,
            "category": "appetizer|main|dessert|drink|salad|soup",
            "description": "Detailed description",
            "ingredients": [
                {{
                    "name": "specific ingredient",
                    "quantity": "amount mentioned",
                    "preparation": "how it's prepared",
                    "category": "protein|vegetable|grain|dairy|spice|oil"
                }}
            ],
            "allergens": ["nuts", "dairy", "gluten"],
            "dietary_tags": ["vegetarian", "gluten-free"],
            "spiciness_level": "mild|medium|hot",
            "preparation_time": "minutes if mentioned"
        }}
    ],
    "menu_sections": [
        {{
            "name": "Appetizers",
            "description": "Section description",
            "item_count": 5
        }}
    ],
    "extraction_metadata": {{
        "total_items": 15,
        "extraction_confidence": 0.92,
        "processing_time_seconds": 3.2,
        "language": "{language}"
    }}
}}

CRITICAL REQUIREMENTS:
- Extract EVERY ingredient mentioned, even if implied
- Be specific with ingredient names (e.g., "chicken breast" not "chicken")
- Include quantities when mentioned (cups, grams, tbsp, etc.)
- Identify preparation methods (grilled, sautéed, roasted, etc.)
- Note all allergens and dietary restrictions
- Return only valid JSON, no additional text
"""

    def _parse_menu_json(self, content: str) -> Dict[str, Any]:
        """Parse JSON response from LLM"""
        try:
            # Clean JSON
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse menu JSON: {e}")
            return self._create_fallback_menu_data("")

    def _enrich_with_ingredients(self, menu_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich menu data with Supabase ingredient database"""
        if not self.supabase:
            logger.warning("Supabase not available - skipping ingredient enrichment")
            return menu_data

        try:
            enriched_items = []

            for item in menu_data.get("menu_items", []):
                ingredients = item.get("ingredients", [])

                # Match each ingredient against database
                enriched_ingredients = []
                for ingredient in ingredients:
                    if isinstance(ingredient, dict) and "name" in ingredient:
                        matched_ingredient = self._match_ingredient(ingredient["name"])
                        if matched_ingredient:
                            # Merge extracted data with database info
                            enriched_ingredient = {
                                **ingredient,
                                **matched_ingredient,
                                "matched_from_db": True
                            }
                        else:
                            enriched_ingredient = {
                                **ingredient,
                                "matched_from_db": False
                            }
                        enriched_ingredients.append(enriched_ingredient)

                # Update item with enriched ingredients
                item["ingredients"] = enriched_ingredients

                # Calculate comprehensive dietary information
                item["dietary_info"] = self._calculate_comprehensive_dietary_info(enriched_ingredients)

                # Add nutritional estimate based on ingredients
                item["nutritional_estimate"] = self._estimate_nutrition(enriched_ingredients)

                enriched_items.append(item)

            menu_data["menu_items"] = enriched_items
            menu_data["enrichment_metadata"] = {
                "ingredients_matched": sum(1 for item in enriched_items
                                         for ing in item.get("ingredients", [])
                                         if ing.get("matched_from_db")),
                "total_ingredients": sum(len(item.get("ingredients", [])) for item in enriched_items),
                "enrichment_timestamp": json.dumps({"timestamp": "now"}, default=str)
            }

            return menu_data

        except Exception as e:
            logger.error(f"Failed to enrich with ingredients: {e}")
            return menu_data

    def _match_ingredient(self, ingredient_name: str) -> Optional[Dict[str, Any]]:
        """Match ingredient against Supabase database"""
        try:
            # Use fuzzy search function
            result = self.supabase.rpc(
                'find_ingredient_matches',
                {'search_text': ingredient_name.lower(), 'max_results': 1}
            ).execute()

            if result.data and len(result.data) > 0:
                match = result.data[0]

                # Get full ingredient details
                ingredient_details = self.supabase.table('ingredients').select('*').eq('id', match['ingredient_id']).execute()

                if ingredient_details.data and len(ingredient_details.data) > 0:
                    ingredient = ingredient_details.data[0]
                    return {
                        "database_id": ingredient['id'],
                        "category": ingredient['category'],
                        "common_names": ingredient.get('common_names', []),
                        "nutritional_info": ingredient.get('nutritional_info', {}),
                        "allergens": ingredient.get('allergens', []),
                        "health_benefits": ingredient.get('health_benefits', []),
                        "health_concerns": ingredient.get('health_concerns', []),
                        "is_vegetarian": ingredient.get('is_vegetarian', True),
                        "is_vegan": ingredient.get('is_vegan', True),
                        "is_gluten_free": ingredient.get('is_gluten_free', True),
                        "is_dairy_free": ingredient.get('is_dairy_free', True),
                        "match_confidence": float(match['confidence_score']),
                        "match_source": "supabase_fuzzy_search"
                    }

        except Exception as e:
            logger.error(f"Failed to match ingredient '{ingredient_name}': {e}")

        return None

    def _calculate_comprehensive_dietary_info(self, ingredients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate detailed dietary information from ingredients"""
        dietary_info = {
            "is_vegetarian": True,
            "is_vegan": True,
            "is_gluten_free": True,
            "is_dairy_free": True,
            "is_nut_free": True,
            "is_soy_free": True,
            "contains_meat": False,
            "contains_poultry": False,
            "contains_fish": False,
            "contains_shellfish": False,
            "contains_eggs": False,
            "contains_dairy": False,
            "contains_gluten": False,
            "contains_nuts": False,
            "contains_soy": False,
            "contains_wheat": False,
            "spiciness_level": "mild"
        }

        for ingredient in ingredients:
            name_lower = ingredient.get("name", "").lower()

            # Check matched database info first
            if ingredient.get("matched_from_db"):
                dietary_info["is_vegetarian"] = dietary_info["is_vegetarian"] and ingredient.get("is_vegetarian", True)
                dietary_info["is_vegan"] = dietary_info["is_vegan"] and ingredient.get("is_vegan", True)
                dietary_info["is_gluten_free"] = dietary_info["is_gluten_free"] and ingredient.get("is_gluten_free", True)
                dietary_info["is_dairy_free"] = dietary_info["is_dairy_free"] and ingredient.get("is_dairy_free", True)

                allergens = ingredient.get("allergens", [])
                if "nuts" in allergens:
                    dietary_info["is_nut_free"] = False
                    dietary_info["contains_nuts"] = True
                if "soy" in allergens:
                    dietary_info["is_soy_free"] = False
                    dietary_info["contains_soy"] = True
                if "dairy" in allergens or "milk" in allergens:
                    dietary_info["is_dairy_free"] = False
                    dietary_info["contains_dairy"] = True
                if "gluten" in allergens or "wheat" in allergens:
                    dietary_info["is_gluten_free"] = False
                    dietary_info["contains_gluten"] = True
                    dietary_info["contains_wheat"] = True

            # Fallback text-based analysis
            else:
                if any(meat in name_lower for meat in ["beef", "pork", "lamb", "venison"]):
                    dietary_info["is_vegetarian"] = False
                    dietary_info["is_vegan"] = False
                    dietary_info["contains_meat"] = True
                elif any(poultry in name_lower for poultry in ["chicken", "turkey", "duck"]):
                    dietary_info["is_vegetarian"] = False
                    dietary_info["is_vegan"] = False
                    dietary_info["contains_poultry"] = True
                elif any(fish in name_lower for fish in ["salmon", "tuna", "cod", "fish"]):
                    dietary_info["is_vegetarian"] = False
                    dietary_info["is_vegan"] = False
                    dietary_info["contains_fish"] = True
                elif any(shellfish in name_lower for shellfish in ["shrimp", "crab", "lobster", "mussels"]):
                    dietary_info["is_vegetarian"] = False
                    dietary_info["is_vegan"] = False
                    dietary_info["contains_shellfish"] = True
                elif "egg" in name_lower:
                    dietary_info["is_vegan"] = False
                    dietary_info["contains_eggs"] = True
                elif any(dairy in name_lower for dairy in ["cheese", "milk", "butter", "cream", "yogurt"]):
                    dietary_info["is_vegan"] = False
                    dietary_info["is_dairy_free"] = False
                    dietary_info["contains_dairy"] = True
                elif any(gluten in name_lower for gluten in ["wheat", "flour", "pasta", "bread"]):
                    dietary_info["is_gluten_free"] = False
                    dietary_info["contains_gluten"] = True
                    dietary_info["contains_wheat"] = True
                elif any(nut in name_lower for nut in ["almond", "peanut", "walnut", "cashew", "pecan"]):
                    dietary_info["is_nut_free"] = False
                    dietary_info["contains_nuts"] = True
                elif "soy" in name_lower or "tofu" in name_lower:
                    dietary_info["is_soy_free"] = False
                    dietary_info["contains_soy"] = True

        return dietary_info

    def _estimate_nutrition(self, ingredients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Estimate nutritional information based on ingredients"""
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0

        for ingredient in ingredients:
            # Use database nutritional info if available
            if ingredient.get("matched_from_db") and ingredient.get("nutritional_info"):
                nutrition = ingredient["nutritional_info"]
                # Scale based on quantity if available
                quantity_multiplier = self._parse_quantity_multiplier(ingredient.get("quantity", "1"))

                total_calories += nutrition.get("calories", 0) * quantity_multiplier
                total_protein += nutrition.get("protein", 0) * quantity_multiplier
                total_carbs += nutrition.get("carbs", 0) * quantity_multiplier
                total_fat += nutrition.get("fat", 0) * quantity_multiplier

        return {
            "estimated_calories": round(total_calories),
            "estimated_protein_grams": round(total_protein),
            "estimated_carbs_grams": round(total_carbs),
            "estimated_fat_grams": round(total_fat),
            "estimation_method": "ingredient_based",
            "confidence_level": "medium"
        }

    def _parse_quantity_multiplier(self, quantity: str) -> float:
        """Parse quantity string to multiplier"""
        if not quantity or quantity == "to taste":
            return 1.0

        quantity = quantity.lower().strip()

        # Common quantity mappings
        quantity_map = {
            "cup": 1.0, "cups": 1.0,
            "tbsp": 0.0625, "tablespoon": 0.0625, "tablespoons": 0.0625,
            "tsp": 0.0208, "teaspoon": 0.0208, "teaspoons": 0.0208,
            "oz": 0.125, "ounce": 0.125, "ounces": 0.125,
            "lb": 1.0, "pound": 1.0, "pounds": 1.0,
            "g": 0.0022, "gram": 0.0022, "grams": 0.0022,
            "kg": 2.2, "kilogram": 2.2, "kilograms": 2.2
        }

        # Extract number and unit
        match = re.match(r'(\d*\.?\d+)\s*(.*)', quantity)
        if match:
            number = float(match.group(1))
            unit = match.group(2).strip()

            base_multiplier = quantity_map.get(unit, 1.0)
            return number * base_multiplier

        return 1.0

    def _optimize_for_mobile_delivery(self, menu_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize data structure for efficient mobile delivery"""
        # Add mobile-specific optimizations
        menu_data["mobile_optimization"] = {
            "compressed_ingredients": True,
            "cached_at": json.dumps({"timestamp": "now"}, default=str),
            "sync_version": "1.0",
            "estimated_payload_size_kb": len(json.dumps(menu_data)) / 1024
        }

        # Ensure all required fields are present for mobile apps
        for item in menu_data.get("menu_items", []):
            item.setdefault("ingredients", [])
            item.setdefault("dietary_info", {})
            item.setdefault("allergens", [])
            item.setdefault("nutritional_estimate", {})

        return menu_data

    def _create_fallback_menu_data(self, ocr_text: str) -> Dict[str, Any]:
        """Create basic fallback menu data"""
        lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]

        menu_items = []
        for line in lines[:10]:
            if len(line) > 3:
                menu_items.append({
                    "name": line,
                    "price": None,
                    "category": "unknown",
                    "description": "",
                    "ingredients": [],
                    "allergens": [],
                    "dietary_info": {},
                    "nutritional_estimate": {}
                })

        return {
            "restaurant_info": {
                "name": "Unknown Restaurant",
                "cuisine_type": "Unknown",
                "location": "",
                "price_range": "",
                "specialties": []
            },
            "menu_items": menu_items,
            "menu_sections": [],
            "extraction_metadata": {
                "total_items": len(menu_items),
                "extraction_confidence": 0.1,
                "processing_time_seconds": 0.0,
                "language": "en",
                "fallback_used": True
            }
        }

    def _create_empty_response(self) -> Dict[str, Any]:
        """Create empty response for no data found"""
        return {
            "restaurant_info": {},
            "menu_items": [],
            "menu_sections": [],
            "extraction_metadata": {
                "total_items": 0,
                "extraction_confidence": 0.0,
                "processing_time_seconds": 0.0,
                "error": "No menu items found in OCR text"
            }
        }

    def _create_error_response(self, error: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            "restaurant_info": {},
            "menu_items": [],
            "menu_sections": [],
            "extraction_metadata": {
                "total_items": 0,
                "extraction_confidence": 0.0,
                "processing_time_seconds": 0.0,
                "error": error
            }
        }