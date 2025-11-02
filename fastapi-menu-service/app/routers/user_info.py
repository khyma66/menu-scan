"""User info router with health conditions joined."""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
from app.routers.auth import get_current_user

router = APIRouter(prefix="/user-info", tags=["User Info"])


@router.get("/")
async def get_user_info_with_conditions(current_user: dict = Depends(get_current_user)):
    """
    Get user information with health conditions joined.
    
    Returns user profile and all associated health conditions.
    """
    try:
        from app.services.supabase_client import SupabaseClient
        from app.services.health_service import HealthService
        
        supabase = SupabaseClient()
        health_service = HealthService()
        
        user_id = current_user.get("id")
        
        # Get user profile
        user_profile = await health_service.supabase.client.table("users").select("*").eq("id", user_id).single().execute()
        
        if not user_profile.data:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Get health conditions
        health_conditions = await health_service.get_user_health_conditions(user_id)
        
        # Combine user info with health conditions
        return {
            "user": user_profile.data,
            "health_conditions": health_conditions,
            "health_conditions_count": len(health_conditions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user info: {str(e)}")


@router.get("/summary")
async def get_user_summary(current_user: dict = Depends(get_current_user)):
    """
    Get user summary with health conditions count.
    """
    try:
        from app.services.health_service import HealthService
        
        health_service = HealthService()
        user_id = current_user.get("id")
        
        # Get health conditions
        health_conditions = await health_service.get_user_health_conditions(user_id)
        
        # Count by type
        by_type = {
            "allergy": len([c for c in health_conditions if c.get("condition_type") == "allergy"]),
            "illness": len([c for c in health_conditions if c.get("condition_type") == "illness"]),
            "dietary": len([c for c in health_conditions if c.get("condition_type") == "dietary"]),
        }
        
        # Check for specific conditions
        has_fever = any(c.get("condition_name") in ["fever", "flu", "cold"] for c in health_conditions)
        has_gi = any(c.get("condition_name") in ["gastrointestinal", "nausea", "indigestion", "stomach"] for c in health_conditions)
        
        return {
            "user_id": user_id,
            "total_conditions": len(health_conditions),
            "conditions_by_type": by_type,
            "has_fever": has_fever,
            "has_gastrointestinal": has_gi,
            "conditions": health_conditions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user summary: {str(e)}")

