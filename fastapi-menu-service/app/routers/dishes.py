"""Dish management router."""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional, List
from app.services.dish_service import DishService
from app.models import Dish, DishCreateRequest, DishRecommendation
from pydantic import BaseModel

router = APIRouter(prefix="/dishes", tags=["Dishes"])

dish_service = DishService()


async def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """Get current user if token is provided."""
    if not authorization:
        return None
    
    try:
        from app.services.auth_service import AuthService
        auth_service = AuthService()
        token = authorization.replace("Bearer ", "")
        return auth_service.verify_token(token)
    except Exception:
        return None


@router.get("/", response_model=List[Dish])
async def get_all_dishes():
    """Get all dishes with ingredients."""
    try:
        dishes = await dish_service.get_all_dishes()
        return dishes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=dict)
async def create_dish(
    dish: DishCreateRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Create a new dish with ingredients."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        dish_id = await dish_service.create_dish(
            name_original=dish.name_original,
            name_english=dish.name_english,
            description=dish.description,
            category=dish.category,
            price_range=dish.price_range,
            ingredients=dish.ingredients
        )
        
        if not dish_id:
            raise HTTPException(status_code=500, detail="Failed to create dish")
        
        return {"success": True, "dish_id": dish_id, "message": "Dish created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations")
async def get_recommendations(
    conditions: str,  # Comma-separated list
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Get dish recommendations based on health conditions.
    
    Args:
        conditions: Comma-separated list of conditions (e.g., "fever,gastrointestinal")
    """
    try:
        condition_list = [c.strip() for c in conditions.split(",")]
        recommendations = await dish_service.get_dish_recommendations(condition_list)
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/filter")
async def filter_dishes_by_health(
    conditions: str,  # Comma-separated list
    menu_items: str = None,  # JSON string of menu items
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Filter menu items based on health conditions.
    
    Args:
        conditions: Comma-separated list of conditions
        menu_items: JSON string of menu items from OCR
    """
    try:
        import json
        condition_list = [c.strip() for c in conditions.split(",")]
        
        if menu_items:
            items = json.loads(menu_items)
        else:
            items = []
        
        filtered = await dish_service.filter_dishes_by_health(items, condition_list)
        return filtered
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

