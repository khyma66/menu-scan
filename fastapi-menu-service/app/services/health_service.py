"""Health condition and menu suggestion service."""

from typing import List, Dict, Any, Optional
from app.services.supabase_client import SupabaseClient
from app.models import MenuItem
import logging

logger = logging.getLogger(__name__)


class HealthService:
    """Service for managing health conditions and menu suggestions."""
    
    def __init__(self):
        """Initialize services."""
        self.supabase = SupabaseClient()
    
    async def get_user_health_conditions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all health conditions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of health conditions
        """
        try:
            response = self.supabase.client.table("health_conditions").select("*").eq("user_id", user_id).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error getting health conditions: {e}")
            return []
    
    async def add_health_condition(
        self, 
        user_id: str, 
        condition_type: str, 
        condition_name: str, 
        severity: Optional[str] = None,
        description: Optional[str] = None
    ) -> bool:
        """
        Add a health condition for a user.
        
        Args:
            user_id: User ID
            condition_type: Type of condition (allergy/illness/dietary)
            condition_name: Name of condition
            severity: Severity level
            description: Additional description
            
        Returns:
            True if successful
        """
        try:
            # Ensure user exists in users table - create if missing
            try:
                user_check = self.supabase.client.table("users").select("id, email").eq("id", user_id).execute()
                if not user_check.data:
                    logger.warning(f"User {user_id} not found in users table, creating profile")
                    
                    # Try to get user email from auth.users (requires service role)
                    # For now, create with a placeholder - the trigger should handle this,
                    # but if it didn't, we'll create it manually
                    try:
                        # Use upsert (INSERT ... ON CONFLICT DO NOTHING)
                        user_response = self.supabase.client.table("users").upsert({
                            "id": user_id,
                            "email": f"user_{user_id[:8]}@unknown.com",  # Placeholder
                        }, {
                            "on_conflict": "id"
                        }).execute()
                        
                        if user_response.data:
                            logger.info(f"Successfully created user profile for {user_id}")
                        else:
                            # Try direct insert
                            try:
                                user_response = self.supabase.client.table("users").insert({
                                    "id": user_id,
                                    "email": f"user_{user_id[:8]}@unknown.com",
                                }).execute()
                                logger.info(f"Created user profile via direct insert")
                            except Exception as insert_err:
                                logger.error(f"Both upsert and insert failed: {insert_err}")
                                # Don't fail yet - maybe user was created by trigger
                    except Exception as create_error:
                        logger.error(f"Error creating user profile: {create_error}")
                        # Continue anyway - might work if trigger created it
                else:
                    logger.debug(f"User {user_id} exists in users table")
            except Exception as e:
                logger.warning(f"Could not verify/create user: {e}")
            
            # Check if condition already exists for this user
            existing = self.supabase.client.table("health_conditions").select("*").eq("user_id", user_id).eq("condition_name", condition_name).execute()
            if existing.data:
                logger.info(f"Condition {condition_name} already exists for user {user_id}, skipping")
                return True
            
            # Insert health condition
            response = self.supabase.client.table("health_conditions").insert({
                "user_id": user_id,
                "condition_type": condition_type,
                "condition_name": condition_name,
                "severity": severity,
                "description": description,
            }).execute()
            
            if response.data:
                logger.info(f"Successfully added health condition {condition_name} for user {user_id}")
                return True
            else:
                logger.error(f"No data returned when adding health condition")
                return False
        except Exception as e:
            logger.error(f"Error adding health condition: {e}", exc_info=True)
            return False
    
    async def remove_health_condition(self, condition_id: str, user_id: str) -> bool:
        """
        Remove a health condition.
        
        Args:
            condition_id: Condition ID
            user_id: User ID for verification
            
        Returns:
            True if successful
        """
        try:
            response = self.supabase.client.table("health_conditions").delete().eq("id", condition_id).eq("user_id", user_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error removing health condition: {e}")
            return False
    
    async def get_menu_suggestions(self, conditions: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get menu suggestions based on conditions.
        
        Args:
            conditions: List of condition names
            
        Returns:
            Dictionary with 'avoid', 'recommend', 'caution' lists
        """
        suggestions = {"avoid": [], "recommend": [], "caution": []}
        
        try:
            for condition in conditions:
                response = self.supabase.client.table("menu_suggestions").select("*").eq("condition_name", condition).execute()
                
                if response.data:
                    for suggestion in response.data:
                        restriction_type = suggestion.get("restriction_type", "caution")
                        if restriction_type in suggestions:
                            suggestions[restriction_type].append(suggestion)
        except Exception as e:
            logger.error(f"Error getting menu suggestions: {e}")
        
        return suggestions
    
    async def filter_menu_items(self, menu_items: List[MenuItem], user_id: str) -> Dict[str, Any]:
        """
        Filter menu items based on user's health conditions.
        
        Args:
            menu_items: List of extracted menu items
            user_id: User ID
            
        Returns:
            Filtered menu with suggestions
        """
        # Get user's health conditions
        conditions = await self.get_user_health_conditions(user_id)
        
        if not conditions:
            return {
                "original_items": menu_items,
                "filtered_items": menu_items,
                "suggestions": [],
                "allergies": [],
                "recommendations": [],
                "dish_recommendations": {}
            }
        
        # Get condition names
        condition_names = [c.get("condition_name") for c in conditions]
        
        # Check for fever or gastrointestinal symptoms
        has_fever = any(c.get("condition_name") in ["fever", "flu", "cold"] for c in conditions)
        has_gi = any(c.get("condition_name") in ["gastrointestinal", "nausea", "indigestion", "stomach"] for c in conditions)
        
        # Use dish service for recommendations if fever/GI symptoms exist
        dish_recommendations = {}
        if has_fever or has_gi:
            from app.services.dish_service import DishService
            dish_service = DishService()
            
            # Convert MenuItem to dict for filtering
            menu_items_dict = [
                {
                    "name": item.name,
                    "price": item.price,
                    "description": item.description,
                    "category": item.category
                }
                for item in menu_items
            ]
            
            # Get recommendations
            rec_conditions = []
            if has_fever:
                rec_conditions.append("fever")
            if has_gi:
                rec_conditions.append("gastrointestinal")
            
            dish_recommendations = await dish_service.filter_dishes_by_health(menu_items_dict, rec_conditions)
        
        # Get general suggestions
        suggestions = await self.get_menu_suggestions(condition_names)
        
        # Filter items
        avoid_keywords = []
        for suggestion in suggestions.get("avoid", []):
            avoid_keywords.extend(suggestion.get("item_keywords", []))
        
        # Convert keywords to lowercase for matching
        avoid_keywords = [kw.lower() for kw in avoid_keywords]
        
        filtered_items = []
        items_to_avoid = []
        
        for item in menu_items:
            item_text = f"{item.name} {item.description or ''}".lower()
            should_avoid = any(keyword in item_text for keyword in avoid_keywords)
            
            if should_avoid:
                items_to_avoid.append(item)
            else:
                filtered_items.append(item)
        
        return {
            "original_items": menu_items,
            "filtered_items": filtered_items,
            "items_to_avoid": items_to_avoid,
            "suggestions": suggestions,
            "conditions": conditions,
            "dish_recommendations": dish_recommendations,
            "has_fever": has_fever,
            "has_gi": has_gi
        }

