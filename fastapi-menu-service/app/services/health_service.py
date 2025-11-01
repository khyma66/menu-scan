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
            response = self.supabase.client.table("health_conditions").insert({
                "user_id": user_id,
                "condition_type": condition_type,
                "condition_name": condition_name,
                "severity": severity,
                "description": description,
            }).execute()
            return True
        except Exception as e:
            logger.error(f"Error adding health condition: {e}")
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
                "recommendations": []
            }
        
        # Get suggestions
        condition_names = [c.get("condition_name") for c in conditions]
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
            "conditions": conditions
        }

