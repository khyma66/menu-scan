"""Service for managing dishes and recommendations."""

from typing import List, Dict, Any, Optional
from app.services.supabase_client import SupabaseClient
from app.models import Dish, DishRecommendation
import logging

logger = logging.getLogger(__name__)


class DishService:
    """Service for dish management and recommendations."""
    
    def __init__(self):
        """Initialize services."""
        self.supabase = SupabaseClient()
    
    async def get_all_dishes(self) -> List[Dish]:
        """Get all dishes with their ingredients."""
        try:
            response = self.supabase.client.table("dishes").select("*").execute()
            
            dishes = []
            if response.data:
                for dish_data in response.data:
                    # Get ingredients for this dish
                    ingredients_response = self.supabase.client.table("dish_ingredients").select(
                        "ingredients:ingredient_id(name)"
                    ).eq("dish_id", dish_data["id"]).execute()
                    
                    ingredients = []
                    if ingredients_response.data:
                        for di in ingredients_response.data:
                            if di.get("ingredients"):
                                ingredients.append(di["ingredients"]["name"])
                    
                    dish = Dish(
                        id=str(dish_data["id"]),
                        name_original=dish_data["name_original"],
                        name_english=dish_data["name_english"],
                        description=dish_data.get("description"),
                        category=dish_data.get("category"),
                        price_range=dish_data.get("price_range"),
                        ingredients=ingredients
                    )
                    dishes.append(dish)
            
            return dishes
        except Exception as e:
            logger.error(f"Error getting dishes: {e}")
            return []
    
    async def create_dish(
        self,
        name_original: str,
        name_english: str,
        description: Optional[str] = None,
        category: Optional[str] = None,
        price_range: Optional[str] = None,
        ingredients: List[str] = []
    ) -> Optional[str]:
        """Create a new dish with ingredients."""
        try:
            # Create dish
            dish_response = self.supabase.client.table("dishes").insert({
                "name_original": name_original,
                "name_english": name_english,
                "description": description,
                "category": category,
                "price_range": price_range,
            }).execute()
            
            if not dish_response.data:
                return None
            
            dish_id = dish_response.data[0]["id"]
            
            # Add ingredients
            for ingredient_name in ingredients:
                # Check if ingredient exists
                ing_response = self.supabase.client.table("ingredients").select("id").eq("name", ingredient_name).execute()
                
                if ing_response.data:
                    ingredient_id = ing_response.data[0]["id"]
                else:
                    # Create ingredient if it doesn't exist
                    new_ing = self.supabase.client.table("ingredients").insert({
                        "name": ingredient_name
                    }).execute()
                    if new_ing.data:
                        ingredient_id = new_ing.data[0]["id"]
                    else:
                        continue
                
                # Link ingredient to dish
                self.supabase.client.table("dish_ingredients").insert({
                    "dish_id": dish_id,
                    "ingredient_id": ingredient_id,
                    "is_main_ingredient": False
                }).execute()
            
            return str(dish_id)
        except Exception as e:
            logger.error(f"Error creating dish: {e}")
            return None
    
    async def get_dish_recommendations(
        self,
        condition_names: List[str],
        user_id: Optional[str] = None
    ) -> Dict[str, List[DishRecommendation]]:
        """
        Get dish recommendations based on health conditions.
        
        Args:
            condition_names: List of condition names (e.g., ['fever', 'gastrointestinal'])
            user_id: Optional user ID for personalized recommendations
            
        Returns:
            Dictionary with 'recommended', 'not_recommended', 'caution' lists
        """
        recommendations = {
            "recommended": [],
            "not_recommended": [],
            "caution": []
        }
        
        try:
            # Get recommendations for each condition
            for condition in condition_names:
                response = self.supabase.client.table("health_dish_recommendations").select(
                    "*, dishes(*)"
                ).eq("condition_name", condition).execute()
                
                if response.data:
                    for rec_data in response.data:
                        dish_data = rec_data.get("dishes")
                        if not dish_data:
                            continue
                        
                        # Get ingredients
                        ingredients_response = self.supabase.client.table("dish_ingredients").select(
                            "ingredients:ingredient_id(name)"
                        ).eq("dish_id", dish_data["id"]).execute()
                        
                        ingredients = []
                        if ingredients_response.data:
                            for di in ingredients_response.data:
                                if di.get("ingredients"):
                                    ingredients.append(di["ingredients"]["name"])
                        
                        dish = Dish(
                            id=str(dish_data["id"]),
                            name_original=dish_data["name_original"],
                            name_english=dish_data["name_english"],
                            description=dish_data.get("description"),
                            category=dish_data.get("category"),
                            price_range=dish_data.get("price_range"),
                            ingredients=ingredients
                        )
                        
                        recommendation = DishRecommendation(
                            dish=dish,
                            recommendation_type=rec_data["recommendation_type"],
                            reason=rec_data.get("reason")
                        )
                        
                        rec_type = rec_data["recommendation_type"]
                        if rec_type in recommendations:
                            recommendations[rec_type].append(recommendation)
        except Exception as e:
            logger.error(f"Error getting dish recommendations: {e}")
        
        return recommendations
    
    async def filter_dishes_by_health(
        self,
        menu_items: List[Dict[str, Any]],
        condition_names: List[str]
    ) -> Dict[str, Any]:
        """
        Filter menu items based on health conditions.
        
        Args:
            menu_items: List of menu items from OCR
            condition_names: Health conditions to check
            
        Returns:
            Filtered results with recommendations
        """
        # Get recommendations
        recs = await self.get_dish_recommendations(condition_names)
        
        # Convert menu items to lowercase for matching
        menu_lower = {item["name"].lower(): item for item in menu_items}
        
        not_recommended = []
        recommended = []
        neutral = []
        
        for item in menu_items:
            item_name_lower = item["name"].lower()
            item_original_name = item.get("original_name", item["name"]).lower()
            item_english = item["name"]  # Already in English if translated
            
            # Check if this dish is in recommendations
            found_in_recs = False
            
            # Check not recommended - match on both English and original names
            for nr in recs["not_recommended"]:
                dish_english_lower = nr.dish.name_english.lower()
                dish_original_lower = nr.dish.name_original.lower()
                
                # Match on English name
                if (dish_english_lower in item_name_lower or item_name_lower in dish_english_lower or
                    dish_english_lower in item_original_name or item_original_name in dish_english_lower):
                    not_recommended.append({
                        "name": item_english,  # Use English name
                        "original_name": item.get("original_name", item["name"]),
                        "price": item.get("price"),
                        "description": item.get("description"),
                        "category": item.get("category"),
                        "reason": nr.reason,
                        "recommendation": "not_recommended"
                    })
                    found_in_recs = True
                    break
                
                # Match on original name
                if (dish_original_lower in item_name_lower or item_name_lower in dish_original_lower or
                    dish_original_lower in item_original_name or item_original_name in dish_original_lower):
                    not_recommended.append({
                        "name": item_english,
                        "original_name": item.get("original_name", item["name"]),
                        "price": item.get("price"),
                        "description": item.get("description"),
                        "category": item.get("category"),
                        "reason": nr.reason,
                        "recommendation": "not_recommended"
                    })
                    found_in_recs = True
                    break
            
            # Check recommended - match on both English and original names
            if not found_in_recs:
                for r in recs["recommended"]:
                    dish_english_lower = r.dish.name_english.lower()
                    dish_original_lower = r.dish.name_original.lower()
                    
                    # Match on English name
                    if (dish_english_lower in item_name_lower or item_name_lower in dish_english_lower or
                        dish_english_lower in item_original_name or item_original_name in dish_english_lower):
                        recommended.append({
                            "name": item_english,
                            "original_name": item.get("original_name", item["name"]),
                            "price": item.get("price"),
                            "description": item.get("description"),
                            "category": item.get("category"),
                            "reason": r.reason,
                            "recommendation": "recommended"
                        })
                        found_in_recs = True
                        break
                    
                    # Match on original name
                    if (dish_original_lower in item_name_lower or item_name_lower in dish_original_lower or
                        dish_original_lower in item_original_name or item_original_name in dish_original_lower):
                        recommended.append({
                            "name": item_english,
                            "original_name": item.get("original_name", item["name"]),
                            "price": item.get("price"),
                            "description": item.get("description"),
                            "category": item.get("category"),
                            "reason": r.reason,
                            "recommendation": "recommended"
                        })
                        found_in_recs = True
                        break
            
            # Check caution
            if not found_in_recs:
                for c in recs["caution"]:
                    if c.dish.name_english.lower() in item_name_lower or item_name_lower in c.dish.name_english.lower():
                        neutral.append({
                            **item,
                            "reason": c.reason,
                            "recommendation": "caution"
                        })
                        found_in_recs = True
                        break
            
            # If not found in recommendations, it's neutral
            if not found_in_recs:
                neutral.append(item)
        
        return {
            "all_items": menu_items,
            "recommended": recommended,
            "not_recommended": not_recommended,
            "neutral": neutral,
            "conditions": condition_names
        }

