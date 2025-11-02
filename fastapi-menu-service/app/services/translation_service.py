"""Service for translating menu items to English using dish database and storing translations."""

import logging
from typing import List, Dict, Any, Optional
from app.services.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


class TranslationService:
    """Service for translating menu items to English and storing translations."""
    
    def __init__(self):
        """Initialize translation service."""
        self.supabase = SupabaseClient()
    
    async def save_translation(
        self,
        original_text: str,
        original_language: str,
        translated_text: str,
        translation_method: str = "dish_database",
        context: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Save a translation to the database.
        
        Args:
            original_text: Original text in source language
            original_language: Language code (e.g., 'fr', 'es', 'de')
            translated_text: Translated text in English
            translation_method: Method used ('dish_database', 'llm', 'manual')
            context: Additional context (e.g., 'menu_item', 'description')
            user_id: Optional user ID who made the translation
            
        Returns:
            True if saved successfully
        """
        try:
            # Use the upsert function to save or update translation
            response = self.supabase.client.rpc(
                "upsert_translation",
                {
                    "p_original_text": original_text,
                    "p_original_language": original_language,
                    "p_translated_text": translated_text,
                    "p_translation_method": translation_method,
                    "p_context": context,
                    "p_user_id": user_id
                }
            ).execute()
            
            if response.data:
                logger.debug(f"Saved translation: {original_text} -> {translated_text}")
                return True
            return False
        except Exception as e:
            logger.warning(f"Failed to save translation to database: {e}")
            # Don't fail the translation if save fails
            return False
    
    async def get_translation(
        self,
        original_text: str,
        original_language: str
    ) -> Optional[str]:
        """
        Get a translation from the database.
        
        Args:
            original_text: Original text to translate
            original_language: Language code
            
        Returns:
            Translated text or None if not found
        """
        try:
            response = self.supabase.client.table("translations").select(
                "translated_text"
            ).eq("original_text", original_text).eq(
                "original_language", original_language
            ).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0].get("translated_text")
            return None
        except Exception as e:
            logger.debug(f"Translation not found in database: {e}")
            return None
    
    async def translate_menu_items(
        self,
        menu_items: List[Dict[str, Any]],
        detected_language: str = "en",
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Translate menu items to English by matching with dishes in database.
        Saves translations to the translations table.
        
        Args:
            menu_items: List of menu items with name, price, description, category
            detected_language: Language code of the source text (e.g., 'fr', 'es', 'de')
            user_id: Optional user ID for tracking translations
            
        Returns:
            List of menu items with English names (name field updated to English)
        """
        try:
            # Skip translation if already English
            if detected_language == "en":
                # Still check for saved translations in case some items need translation
                translated_items = []
                for item in menu_items:
                    item_name = item.get("name", "").strip()
                    if item_name:
                        # Check if there's a saved translation
                        saved_translation = await self.get_translation(item_name, "en")
                        if saved_translation and saved_translation != item_name:
                            item["name"] = saved_translation
                            item["original_name"] = item_name
                    translated_items.append(item)
                return translated_items
            
            # Get all dishes from database
            dishes_response = self.supabase.client.table("dishes").select("*").execute()
            dishes = dishes_response.data if dishes_response.data else []
            
            # Create lookup maps
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
                # Ensure item is a dict, not an object
                if not isinstance(item, dict):
                    item = {
                        "name": getattr(item, "name", ""),
                        "price": getattr(item, "price", None),
                        "description": getattr(item, "description", None),
                        "category": getattr(item, "category", None)
                    }
                
                item_name = item.get("name", "").strip()
                if not item_name:
                    # Still add item even if no name
                    translated_items.append({
                        "name": item.get("name", ""),
                        "price": item.get("price"),
                        "description": item.get("description"),
                        "category": item.get("category"),
                        "original_name": item.get("name", "")
                    })
                    continue
                
                item_name_lower = item_name.lower()
                translated_item = item.copy()
                translation_found = False
                translated_text = item_name  # Default to original
                
                # First, check database for saved translation
                saved_translation = await self.get_translation(item_name, detected_language)
                if saved_translation:
                    translated_text = saved_translation
                    translated_item["name"] = translated_text
                    translated_item["original_name"] = item_name
                    translation_found = True
                # Try exact match with dish original name
                elif item_name_lower in original_name_map:
                    dish = original_name_map[item_name_lower]
                    translated_text = dish.get("name_english", item_name)
                    translated_item["name"] = translated_text
                    translated_item["original_name"] = item_name
                    translation_found = True
                # Try partial match with original name
                elif not translation_found:
                    for orig, dish in original_name_map.items():
                        if item_name_lower in orig or orig in item_name_lower:
                            if len(orig) > 3:  # Avoid very short matches
                                translated_text = dish.get("name_english", item_name)
                                translated_item["name"] = translated_text
                                translated_item["original_name"] = item_name
                                translation_found = True
                                break
                
                # If no match with original, try exact match with English name
                if not translation_found and item_name_lower in english_name_map:
                    # Already in English
                    translated_text = item_name
                    translated_item["name"] = item_name
                    translated_item["original_name"] = item_name
                    translation_found = True
                
                # Use description if available
                if not translation_found and item.get("description"):
                    desc_lower = item.get("description", "").lower()
                    for orig, dish in original_name_map.items():
                        if orig in desc_lower or desc_lower in orig:
                            translated_text = dish.get("name_english", item_name)
                            translated_item["name"] = translated_text
                            translated_item["original_name"] = item_name
                            translation_found = True
                            break
                
                # If still no match, keep original name
                if not translation_found:
                    translated_item["name"] = item_name
                    translated_item["original_name"] = item_name
                    translated_text = item_name
                
                # Save translation to database if translation was found
                if translation_found and translated_text != item_name:
                    await self.save_translation(
                        original_text=item_name,
                        original_language=detected_language,
                        translated_text=translated_text,
                        translation_method="dish_database",
                        context="menu_item",
                        user_id=user_id
                    )
                
                # Update description if dish has better description
                if translation_found:
                    dish_obj = original_name_map.get(item_name_lower) or english_name_map.get(item_name_lower)
                    if dish_obj:
                        dish_description = dish_obj.get("description")
                        if dish_description and not translated_item.get("description"):
                            translated_item["description"] = dish_description
                        if dish_obj.get("category") and not translated_item.get("category"):
                            translated_item["category"] = dish_obj.get("category")
                
                # Ensure all required fields are present as dict keys
                translated_item.setdefault("name", item_name)
                translated_item.setdefault("original_name", item_name)
                translated_item.setdefault("price", item.get("price"))
                translated_item.setdefault("description", item.get("description"))
                translated_item.setdefault("category", item.get("category"))
                
                translated_items.append(translated_item)
            
            return translated_items
            
        except Exception as e:
            logger.error(f"Error translating menu items: {e}")
            # Return original items if translation fails
            return menu_items

