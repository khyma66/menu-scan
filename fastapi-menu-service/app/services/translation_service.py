"""Service for translating menu items to English using dish database."""

import logging
from typing import List, Dict, Any, Optional
from app.services.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


class TranslationService:
    """Service for translating menu items to English."""
    
    def __init__(self):
        """Initialize translation service."""
        self.supabase = SupabaseClient()
    
    async def translate_menu_items(self, menu_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Translate menu items to English by matching with dishes in database.
        
        Args:
            menu_items: List of menu items with name, price, description, category
            
        Returns:
            List of menu items with English names (name field updated to English)
        """
        try:
            # Get all dishes from database
            dishes_response = self.supabase.client.table("dishes").select("*").execute()
            dishes = dishes_response.data if dishes_response.data else []
            
            # Create lookup maps
            # Map from original name (lowercase) to dish
            original_name_map = {}
            english_name_map = {}
            
            for dish in dishes:
                original_lower = dish.get("name_original", "").lower().strip()
                english_lower = dish.get("name_english", "").lower().strip()
                
                if original_lower:
                    original_name_map[original_lower] = dish
                if english_lower:
                    english_name_map[english_lower] = dish
            
            # Translate each menu item
            translated_items = []
            for item in menu_items:
                item_name = item.get("name", "").strip()
                item_name_lower = item_name.lower()
                
                translated_item = item.copy()
                translation_found = False
                
                # First, try exact match with original name
                if item_name_lower in original_name_map:
                    dish = original_name_map[item_name_lower]
                    translated_item["name"] = dish.get("name_english", item_name)
                    translated_item["original_name"] = item_name  # Keep original
                    translation_found = True
                # Try partial match with original name
                elif not translation_found:
                    for orig, dish in original_name_map.items():
                        if item_name_lower in orig or orig in item_name_lower:
                            if len(orig) > 3:  # Avoid very short matches
                                translated_item["name"] = dish.get("name_english", item_name)
                                translated_item["original_name"] = item_name
                                translation_found = True
                                break
                
                # If no match with original, try exact match with English name
                if not translation_found and item_name_lower in english_name_map:
                    # Already in English
                    translated_item["name"] = item_name
                    translation_found = True
                
                # Use description if available
                if not translation_found and item.get("description"):
                    desc_lower = item.get("description", "").lower()
                    for orig, dish in original_name_map.items():
                        if orig in desc_lower or desc_lower in orig:
                            translated_item["name"] = dish.get("name_english", item_name)
                            translated_item["original_name"] = item_name
                            translation_found = True
                            break
                
                # If still no match, keep original name but mark it
                if not translation_found:
                    translated_item["name"] = item_name
                    translated_item["original_name"] = item_name
                
                # Update description if dish has better description
                dish_description = None
                if translation_found:
                    dish_obj = original_name_map.get(item_name_lower) or english_name_map.get(item_name_lower)
                    if dish_obj:
                        dish_description = dish_obj.get("description")
                        if dish_description and not translated_item.get("description"):
                            translated_item["description"] = dish_description
                        if dish_obj.get("category") and not translated_item.get("category"):
                            translated_item["category"] = dish_obj.get("category")
                
                translated_items.append(translated_item)
            
            return translated_items
            
        except Exception as e:
            logger.error(f"Error translating menu items: {e}")
            # Return original items if translation fails
            return menu_items

