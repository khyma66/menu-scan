"""Authentication router."""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
from app.services.auth_service import AuthService
from app.models import ErrorResponse
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

auth_service = AuthService()


class UserProfile(BaseModel):
    """User profile model."""
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None


class HealthConditionInput(BaseModel):
    """Health condition input model."""
    condition_type: str  # allergy, illness, dietary
    condition_name: str
    severity: Optional[str] = None
    description: Optional[str] = None


async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Get current user from authorization header.
    
    Args:
        authorization: Authorization header with Bearer token
        
    Returns:
        User data or raises HTTPException
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    token = authorization.replace("Bearer ", "")
    if not token or token == "Bearer":
        raise HTTPException(status_code=401, detail="Token missing")
    
    user = await auth_service.verify_token(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return user


@router.get("/test")
async def test_auth():
    """Test endpoint - no auth required."""
    return {"message": "Auth router is working", "status": "ok"}


@router.get("/user")
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user's profile."""
    try:
        profile = await auth_service.get_user_profile(current_user.get("id"))
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profile")
async def update_profile(
    profile: UserProfile,
    current_user: dict = Depends(get_current_user)
):
    """Update user profile."""
    try:
        success = await auth_service.update_user_profile(
            current_user.get("id"),
            profile.model_dump(exclude_unset=True)
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update profile")
        return {"message": "Profile updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health-conditions")
async def get_health_conditions(current_user: dict = Depends(get_current_user)):
    """Get user's health conditions."""
    try:
        from app.services.health_service import HealthService
        health_service = HealthService()
        conditions = await health_service.get_user_health_conditions(current_user.get("id"))
        return conditions
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error getting health conditions: {str(e)}")


@router.post("/health-conditions")
async def add_health_condition(
    condition: HealthConditionInput,
    current_user: dict = Depends(get_current_user)
):
    """Add a health condition."""
    try:
        from app.services.health_service import HealthService
        from app.services.auth_service import AuthService
        
        user_id = current_user.get("id")
        user_email = current_user.get("email")
        
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in token")
        
        # Ensure user profile exists before adding health condition
        auth_service = AuthService()
        profile = await auth_service.get_user_profile(user_id)
        if not profile:
            # Create user profile
            logger.info(f"Creating user profile for {user_id}")
            created = await auth_service.create_user_profile(
                user_id,
                user_email or f"user_{user_id[:8]}@unknown.com",
                current_user.get("user_metadata", {}).get("full_name")
            )
            if not created:
                logger.warning(f"Failed to create user profile for {user_id}, continuing anyway")
        
        health_service = HealthService()
        success = await health_service.add_health_condition(
            user_id,
            condition.condition_type,
            condition.condition_name,
            condition.severity,
            condition.description
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add condition")
        return {"message": "Condition added successfully", "condition": condition.model_dump()}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error adding condition: {str(e)}")


@router.delete("/health-conditions/{condition_id}")
async def remove_health_condition(
    condition_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove a health condition."""
    try:
        from app.services.health_service import HealthService
        health_service = HealthService()
        success = await health_service.remove_health_condition(condition_id, current_user.get("id"))
        if not success:
            raise HTTPException(status_code=500, detail="Failed to remove condition")
        return {"message": "Condition removed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
