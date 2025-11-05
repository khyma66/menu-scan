"""New Health Router - Complete rewrite with robust API endpoints."""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
import logging

from app.services.new_health_service import (
    HealthService, HealthCondition, HealthProfile,
    HealthValidationError, HealthServiceError
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


# Pydantic models for API
class HealthConditionRequest(BaseModel):
    """Request model for health condition."""
    condition_type: str = Field(..., description="Type of condition: allergy, illness, dietary, preference")
    condition_name: str = Field(..., description="Name of the condition")
    severity: Optional[str] = Field(None, description="Severity: mild, moderate, severe")
    description: Optional[str] = Field(None, description="Additional description")

    @validator('condition_type')
    def validate_condition_type(cls, v):
        valid_types = {'allergy', 'illness', 'dietary', 'preference'}
        if v not in valid_types:
            raise ValueError(f'Condition type must be one of: {valid_types}')
        return v

    @validator('severity')
    def validate_severity(cls, v):
        if v is not None:
            valid_severities = {'mild', 'moderate', 'severe'}
            if v not in valid_severities:
                raise ValueError(f'Severity must be one of: {valid_severities}')
        return v


class HealthConditionResponse(BaseModel):
    """Response model for health condition."""
    id: str
    condition_type: str
    condition_name: str
    severity: Optional[str]
    description: Optional[str]
    created_at: str


class HealthProfileResponse(BaseModel):
    """Response model for health profile."""
    id: str
    user_id: str
    profile_name: Optional[str]
    is_active: bool
    conditions: List[HealthConditionResponse]
    created_at: str
    updated_at: str


class HealthRecommendationRequest(BaseModel):
    """Request model for health recommendations."""
    menu_items: List[Dict[str, Any]] = Field(..., description="List of menu items to analyze")


class HealthRecommendationResponse(BaseModel):
    """Response model for health recommendations."""
    recommendations: List[Dict[str, Any]]
    total_items: int
    analyzed_conditions: int
    generated_at: str


class HealthAnalyticsResponse(BaseModel):
    """Response model for health analytics."""
    total_actions: int
    conditions_by_type: Dict[str, int]
    recent_activity: List[Dict[str, Any]]


# Import get_current_user at the top to avoid circular imports
from app.routers.auth import get_current_user

# Dependency injection
def get_health_service() -> HealthService:
    """Get health service instance."""
    return HealthService()


@router.post("/profile", response_model=Dict[str, Any])
async def create_health_profile(
    profile_name: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    health_service: HealthService = Depends(get_health_service)
):
    """
    Create a health profile for the current user.

    - Creates a new health profile if one doesn't exist
    - Returns existing profile if already created
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        profile = await health_service.profile_manager.create_profile(user_id, profile_name)

        return {
            "success": True,
            "profile": {
                "id": profile.id,
                "user_id": profile.user_id,
                "profile_name": profile.profile_name,
                "is_active": profile.is_active,
                "conditions_count": len(profile.conditions)
            },
            "message": "Health profile created successfully"
        }

    except HealthServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating health profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/profile", response_model=HealthProfileResponse)
async def get_health_profile(
    current_user: dict = Depends(get_current_user),
    health_service: HealthService = Depends(get_health_service)
):
    """
    Get the current user's health profile with all conditions.
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        profile = await health_service.get_user_health_profile(user_id)

        if not profile:
            raise HTTPException(status_code=404, detail="Health profile not found")

        return HealthProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
            profile_name=profile.profile_name,
            is_active=profile.is_active,
            conditions=[
                HealthConditionResponse(
                    id=f"{cond.condition_type}_{cond.condition_name}",  # Generate ID for response
                    condition_type=cond.condition_type,
                    condition_name=cond.condition_name,
                    severity=cond.severity,
                    description=cond.description,
                    created_at=""  # Would need to track this in the database
                )
                for cond in profile.conditions
            ],
            created_at="",  # Would need to track this in the database
            updated_at=""
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting health profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to get health profile")


@router.post("/conditions", response_model=Dict[str, Any])
async def add_health_condition(
    condition: HealthConditionRequest,
    current_user: dict = Depends(get_current_user),
    health_service: HealthService = Depends(get_health_service)
):
    """
    Add a health condition to the user's profile.

    - Validates input data
    - Checks for duplicates
    - Creates profile if it doesn't exist
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Convert to service model
        health_condition = HealthCondition(
            condition_type=condition.condition_type,
            condition_name=condition.condition_name,
            severity=condition.severity,
            description=condition.description
        )

        condition_id = await health_service.add_health_condition(user_id, health_condition)

        return {
            "success": True,
            "condition_id": condition_id,
            "condition": condition.dict(),
            "message": f"Health condition '{condition.condition_name}' added successfully"
        }

    except HealthValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HealthServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error adding health condition: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/conditions/{condition_name}", response_model=Dict[str, Any])
async def remove_health_condition(
    condition_name: str,
    current_user: dict = Depends(get_current_user),
    health_service: HealthService = Depends(get_health_service)
):
    """
    Remove a health condition from the user's profile.

    - Performs soft delete (marks as inactive)
    - Validates ownership
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        success = await health_service.remove_health_condition(user_id, condition_name)

        if not success:
            raise HTTPException(status_code=404, detail=f"Health condition '{condition_name}' not found")

        return {
            "success": True,
            "message": f"Health condition '{condition_name}' removed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing health condition: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove health condition")


@router.post("/recommendations", response_model=HealthRecommendationResponse)
async def get_health_recommendations(
    request: HealthRecommendationRequest,
    current_user: dict = Depends(get_current_user),
    health_service: HealthService = Depends(get_health_service)
):
    """
    Get health-based recommendations for menu items.

    - Analyzes menu items against user's health conditions
    - Uses caching for performance
    - Tracks analytics
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        recommendations = await health_service.get_health_recommendations(user_id, request.menu_items)

        return HealthRecommendationResponse(**recommendations)

    except Exception as e:
        logger.error(f"Error getting health recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get health recommendations")


@router.get("/analytics", response_model=HealthAnalyticsResponse)
async def get_health_analytics(
    current_user: dict = Depends(get_current_user),
    health_service: HealthService = Depends(get_health_service)
):
    """
    Get health analytics for the current user.

    - Shows usage statistics
    - Recent activity
    - Condition distribution
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        analytics = await health_service.get_user_analytics(user_id)

        return HealthAnalyticsResponse(**analytics)

    except Exception as e:
        logger.error(f"Error getting health analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get health analytics")


@router.get("/conditions", response_model=List[HealthConditionResponse])
async def list_health_conditions(
    current_user: dict = Depends(get_current_user),
    health_service: HealthService = Depends(get_health_service)
):
    """
    List all health conditions for the current user.
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        profile = await health_service.get_user_health_profile(user_id)

        if not profile:
            return []

        return [
            HealthConditionResponse(
                id=f"{cond.condition_type}_{cond.condition_name}",
                condition_type=cond.condition_type,
                condition_name=cond.condition_name,
                severity=cond.severity,
                description=cond.description,
                created_at=""
            )
            for cond in profile.conditions
        ]

    except Exception as e:
        logger.error(f"Error listing health conditions: {e}")
        raise HTTPException(status_code=500, detail="Failed to list health conditions")


# Import get_current_user at the end to avoid circular imports
from app.routers.auth import get_current_user

# Also import the HealthService
from app.services.new_health_service import HealthService