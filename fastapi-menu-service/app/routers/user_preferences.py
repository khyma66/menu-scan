"""User preferences and food preferences router."""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging

from app.routers.auth import get_current_user
from app.services.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user/preferences", tags=["User Preferences"])

# Pydantic models
class FoodPreferenceRequest(BaseModel):
    """Request model for food preferences."""
    preference_type: str = Field(..., description="Type: favorite, disliked, neutral")
    food_category: str = Field(..., description="Food category (e.g., spicy, sweet, savory)")
    food_item: Optional[str] = Field(None, description="Specific food item")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5")
    notes: Optional[str] = Field(None, description="Additional notes")

class FoodPreferenceResponse(BaseModel):
    """Response model for food preferences."""
    id: str
    preference_type: str
    food_category: str
    food_item: Optional[str]
    rating: int
    notes: Optional[str]
    created_at: str

class UserPreferencesResponse(BaseModel):
    """Response model for user preferences."""
    user_id: str
    food_preferences: List[FoodPreferenceResponse]
    dietary_restrictions: List[str]
    favorite_cuisines: List[str]
    spice_tolerance: Optional[str]
    budget_preference: Optional[str]

@router.post("/food-preferences", response_model=Dict[str, Any])
async def add_food_preference(
    preference: FoodPreferenceRequest,
    current_user: dict = Depends(get_current_user)
):
    """Add a food preference for the current user."""
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        supabase = SupabaseClient()

        # Add to food_preferences table
        preference_data = {
            "user_id": user_id,
            "preference_type": preference.preference_type,
            "food_category": preference.food_category,
            "food_item": preference.food_item,
            "rating": preference.rating,
            "notes": preference.notes
        }

        response = supabase.client.table("food_preferences").insert(preference_data).execute()

        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to add food preference")

        return {
            "success": True,
            "preference_id": response.data[0]['id'],
            "message": "Food preference added successfully"
        }

    except Exception as e:
        logger.error(f"Error adding food preference: {e}")
        raise HTTPException(status_code=500, detail="Failed to add food preference")

@router.get("/food-preferences", response_model=List[FoodPreferenceResponse])
async def get_food_preferences(
    current_user: dict = Depends(get_current_user)
):
    """Get all food preferences for the current user."""
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        supabase = SupabaseClient()

        response = supabase.client.table("food_preferences").select("*").eq("user_id", user_id).execute()

        preferences = []
        for pref in response.data or []:
            preferences.append(FoodPreferenceResponse(
                id=pref['id'],
                preference_type=pref['preference_type'],
                food_category=pref['food_category'],
                food_item=pref.get('food_item'),
                rating=pref['rating'],
                notes=pref.get('notes'),
                created_at=pref['created_at']
            ))

        return preferences

    except Exception as e:
        logger.error(f"Error getting food preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to get food preferences")

@router.delete("/food-preferences/{preference_id}", response_model=Dict[str, Any])
async def remove_food_preference(
    preference_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove a food preference."""
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        supabase = SupabaseClient()

        response = supabase.client.table("food_preferences").delete().eq("id", preference_id).eq("user_id", user_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Food preference not found")

        return {
            "success": True,
            "message": "Food preference removed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing food preference: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove food preference")

@router.put("/profile", response_model=Dict[str, Any])
async def update_user_profile(
    dietary_restrictions: Optional[List[str]] = None,
    favorite_cuisines: Optional[List[str]] = None,
    spice_tolerance: Optional[str] = None,
    budget_preference: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Update user profile preferences."""
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        supabase = SupabaseClient()

        # Update or insert user preferences
        profile_data = {
            "user_id": user_id,
            "dietary_restrictions": dietary_restrictions or [],
            "favorite_cuisines": favorite_cuisines or [],
            "spice_tolerance": spice_tolerance,
            "budget_preference": budget_preference
        }

        response = supabase.client.table("user_preferences").upsert(profile_data, {
            "on_conflict": "user_id"
        }).execute()

        return {
            "success": True,
            "message": "User profile updated successfully"
        }

    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user profile")

@router.get("/profile", response_model=UserPreferencesResponse)
async def get_user_profile(
    current_user: dict = Depends(get_current_user)
):
    """Get user profile and preferences."""
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        supabase = SupabaseClient()

        # Get user preferences
        profile_response = supabase.client.table("user_preferences").select("*").eq("user_id", user_id).execute()
        profile_data = profile_response.data[0] if profile_response.data else {}

        # Get food preferences
        food_prefs_response = supabase.client.table("food_preferences").select("*").eq("user_id", user_id).execute()

        food_preferences = []
        for pref in food_prefs_response.data or []:
            food_preferences.append(FoodPreferenceResponse(
                id=pref['id'],
                preference_type=pref['preference_type'],
                food_category=pref['food_category'],
                food_item=pref.get('food_item'),
                rating=pref['rating'],
                notes=pref.get('notes'),
                created_at=pref['created_at']
            ))

        return UserPreferencesResponse(
            user_id=user_id,
            food_preferences=food_preferences,
            dietary_restrictions=profile_data.get('dietary_restrictions', []),
            favorite_cuisines=profile_data.get('favorite_cuisines', []),
            spice_tolerance=profile_data.get('spice_tolerance'),
            budget_preference=profile_data.get('budget_preference')
        )

    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user profile")