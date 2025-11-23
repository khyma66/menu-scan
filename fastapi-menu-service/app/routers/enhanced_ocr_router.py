"""Enhanced OCR router with OpenRouter integration and improved error handling."""

import time
import logging
import os
from fastapi import APIRouter, HTTPException, status, Header, Depends, UploadFile, File, Form
from typing import Optional
from app.models import OCRRequest, OCRResponse, ErrorResponse
from app.services.supabase_client import SupabaseClient
from app.services.enhanced_ocr_service import EnhancedOCRService
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/enhanced-ocr", tags=["Enhanced OCR"])

# Initialize enhanced OCR service
enhanced_ocr = EnhancedOCRService()

def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[dict]:
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

@router.post("/process-upload", response_model=OCRResponse)
async def process_enhanced_image_upload(
    image: UploadFile = File(...),
    enhancement_level: str = Form("high"),  # fast, balanced, high
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Process uploaded menu image using enhanced OCR with OpenRouter/Qwen integration.
    
    This endpoint uses a multi-stage approach:
    1. MLToolkit OCR (if available)
    2. Tesseract OCR with language detection
    3. OpenRouter/Qwen enhancement for better accuracy
    """
    start_time = time.time()
    
    try:
        # Validate file type
        if not image.content_type or not image.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
        
        # Read image data
        img_data = await image.read()
        
        # Verify image size (10MB limit)
        if len(img_data) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Image size exceeds 10MB limit"
            )
        
        # Process with enhanced OCR service
        logger.info(f"Processing image with enhancement level: {enhancement_level}")
        result = await enhanced_ocr.process_image_with_fallback(img_data, enhancement_level)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OCR processing failed: {result.get('error', 'Unknown error')}"
            )
        
        # Extract data from result
        raw_text = result.get("raw_text", "")
        menu_items_data = result.get("menu_items", [])
        processing_metadata = result.get("processing_metadata", {})
        
        if not raw_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No text detected in image"
            )
        
        # Convert menu items to MenuItem objects
        from app.models import MenuItem
        menu_items = []
        for item_data in menu_items_data:
            try:
                menu_items.append(MenuItem(
                    name=str(item_data.get("name", "Unknown Item")),
                    price=item_data.get("price"),
                    description=item_data.get("description"),
                    category=item_data.get("category", "unknown")
                ))
            except Exception as e:
                logger.warning(f"Failed to create MenuItem from {item_data}: {e}")
                # Create a basic MenuItem if conversion fails
                menu_items.append(MenuItem(
                    name="Unknown Item",
                    price=None,
                    description=None,
                    category=None
                ))
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Prepare response data
        response_data = {
            "success": True,
            "menu_items": menu_items,
            "raw_text": raw_text,
            "processing_time_ms": processing_time_ms,
            "enhanced": True,
            "cached": False,
            "metadata": {
                "processing_method": processing_metadata.get("method", "unknown"),
                "enhancement_level": enhancement_level,
                "detected_language": "auto",  # Enhanced service handles this
                "steps_completed": processing_metadata.get("steps", []),
                "confidence": result.get("confidence", 0.0),
                "timestamp": processing_metadata.get("timestamp", ""),
                "processed_by": "enhanced_ocr_service"
            }
        }
        
        # Save to Supabase if user is authenticated
        if current_user:
            try:
                supabase = SupabaseClient()
                serializable_data = response_data.copy()
                serializable_data["menu_items"] = [
                    {
                        "name": item.name,
                        "price": item.price,
                        "description": item.description,
                        "category": item.category
                    }
                    for item in response_data["menu_items"]
                ]
                fake_url = f"enhanced_upload://{image.filename}"
                await supabase.save_ocr_result(fake_url, serializable_data)
                logger.info("OCR result saved to Supabase")
            except Exception as e:
                logger.warning(f"Failed to save to Supabase: {e}")
        
        return OCRResponse(**response_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced OCR processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image: {str(e)}"
        )

@router.post("/process-url", response_model=OCRResponse)
async def process_enhanced_image_url(
    image_url: str = Form(...),
    enhancement_level: str = Form("high"),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Process menu image from URL using enhanced OCR with OpenRouter/Qwen integration.
    """
    start_time = time.time()
    
    try:
        # Download image from URL
        logger.info(f"Processing image from URL: {image_url}")
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        img_data = response.content
        
        # Verify image size
        if len(img_data) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Image size exceeds 10MB limit"
            )
        
        # Process with enhanced OCR service
        result = await enhanced_ocr.process_image_with_fallback(img_data, enhancement_level)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OCR processing failed: {result.get('error', 'Unknown error')}"
            )
        
        # Extract data from result
        raw_text = result.get("raw_text", "")
        menu_items_data = result.get("menu_items", [])
        processing_metadata = result.get("processing_metadata", {})
        
        if not raw_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No text detected in image"
            )
        
        # Convert menu items to MenuItem objects
        from app.models import MenuItem
        menu_items = []
        for item_data in menu_items_data:
            try:
                menu_items.append(MenuItem(
                    name=str(item_data.get("name", "Unknown Item")),
                    price=item_data.get("price"),
                    description=item_data.get("description"),
                    category=item_data.get("category", "unknown")
                ))
            except Exception as e:
                logger.warning(f"Failed to create MenuItem from {item_data}: {e}")
                menu_items.append(MenuItem(
                    name="Unknown Item",
                    price=None,
                    description=None,
                    category=None
                ))
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Prepare response data
        response_data = {
            "success": True,
            "menu_items": menu_items,
            "raw_text": raw_text,
            "processing_time_ms": processing_time_ms,
            "enhanced": True,
            "cached": False,
            "metadata": {
                "processing_method": processing_metadata.get("method", "unknown"),
                "enhancement_level": enhancement_level,
                "detected_language": "auto",
                "steps_completed": processing_metadata.get("steps", []),
                "confidence": result.get("confidence", 0.0),
                "timestamp": processing_metadata.get("timestamp", ""),
                "processed_by": "enhanced_ocr_service"
            }
        }
        
        # Save to Supabase if user is authenticated
        if current_user:
            try:
                supabase = SupabaseClient()
                serializable_data = response_data.copy()
                serializable_data["menu_items"] = [
                    {
                        "name": item.name,
                        "price": item.price,
                        "description": item.description,
                        "category": item.category
                    }
                    for item in response_data["menu_items"]
                ]
                await supabase.save_ocr_result(image_url, serializable_data)
                logger.info("OCR result saved to Supabase")
            except Exception as e:
                logger.warning(f"Failed to save to Supabase: {e}")
        
        return OCRResponse(**response_data)
    
    except requests.RequestException as e:
        logger.error(f"Error downloading image: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to download image: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced OCR URL processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image: {str(e)}"
        )

@router.get("/status")
async def enhanced_ocr_status():
    """Check the status of enhanced OCR service"""
    try:
        # Check if Qwen service is available
        qwen_available = enhanced_ocr._is_qwen_available()

        return {
            "status": "healthy",
            "service": "enhanced_ocr",
            "qwen_available": qwen_available,
            "openrouter_configured": bool(enhanced_ocr.qwen_service.api_key),
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "enhanced_ocr",
            "error": str(e),
            "timestamp": time.time()
        }