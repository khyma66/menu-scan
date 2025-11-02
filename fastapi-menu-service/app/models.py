"""Pydantic models for request and response schemas."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class MenuItem(BaseModel):
    """Individual menu item with price and details."""
    name: str
    price: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None


class Dish(BaseModel):
    """Dish model with ingredients."""
    id: Optional[str] = None
    name_original: str
    name_english: str
    description: Optional[str] = None
    category: Optional[str] = None
    price_range: Optional[str] = None
    ingredients: List[str] = []


class DishRecommendation(BaseModel):
    """Dish recommendation based on health condition."""
    dish: Dish
    recommendation_type: str  # recommended, not_recommended, caution
    reason: Optional[str] = None


class OCRRequest(BaseModel):
    """Request model for OCR processing."""
    image_url: str = Field(..., description="URL of the menu image")
    use_llm_enhancement: bool = Field(True, description="Use LLM to enhance OCR results")
    language: str = Field("auto", description="Expected language of the menu (auto for detection)")


class OCRResponse(BaseModel):
    """Response model for OCR processing."""
    success: bool
    menu_items: List[MenuItem]
    raw_text: str
    processing_time_ms: int
    enhanced: bool = Field(False, description="Whether LLM enhancement was used")
    cached: bool = Field(False, description="Whether result was from cache")
    metadata: Optional[Dict[str, Any]] = None


class DishCreateRequest(BaseModel):
    """Request model for creating a dish."""
    name_original: str
    name_english: str
    description: Optional[str] = None
    category: Optional[str] = None
    price_range: Optional[str] = None
    ingredients: List[str] = []


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str]
