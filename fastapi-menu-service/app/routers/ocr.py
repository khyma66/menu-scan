"""OCR router for processing menu images."""

import time
import logging
from fastapi import APIRouter, HTTPException, status, Header, Depends
from typing import Optional
from typing import Union
from app.models import OCRRequest, OCRResponse, ErrorResponse
from app.services.redis_cache import RedisCache
from app.services.supabase_client import SupabaseClient
from app.services.llm_fallback import LLMFallback
from app.services.health_service import HealthService
from app.utils.ocr_parser import extract_menu_items
from PIL import Image
import requests
import pytesseract
from io import BytesIO

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ocr", tags=["OCR"])


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


@router.post("/process", response_model=OCRResponse)
async def process_image(
    request: OCRRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Process a menu image and extract menu items.
    
    Optionally filters results based on user's health conditions if authenticated.
    
    - **image_url**: URL of the menu image to process
    - **use_llm_enhancement**: Whether to use LLM to enhance OCR results
    - **language**: Expected language of the menu
    """
    start_time = time.time()
    
    try:
        # Check cache first
        cache = RedisCache()
        cached_result = await cache.get(request.image_url)
        
        if cached_result and not current_user:
            logger.info(f"Cache hit for image: {request.image_url}")
            return OCRResponse(**cached_result, cached=True)
        
        # Download and process image
        logger.info(f"Processing image: {request.image_url}")
        response = requests.get(request.image_url, timeout=30)
        response.raise_for_status()
        
        # Verify image size
        img_data = response.content
        if len(img_data) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Image size exceeds 10MB limit"
            )
        
        # Process image with Tesseract OCR
        image = Image.open(BytesIO(img_data))
        raw_text = pytesseract.image_to_string(image, lang=request.language)
        
        if not raw_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No text detected in image"
            )
        
        # Extract menu items from raw text
        menu_items = extract_menu_items(raw_text)
        
        # Use LLM enhancement if requested
        enhanced = False
        if request.use_llm_enhancement:
            llm_service = LLMFallback()
            llm_result = await llm_service.enhance_ocr_result(raw_text, request.language)
            
            if llm_result.get("enhanced"):
                menu_items = llm_result.get("menu_items", menu_items)
                enhanced = True
        
        # Filter based on health conditions if user is authenticated
        if current_user:
            health_service = HealthService()
            filtered_menu = await health_service.filter_menu_items(menu_items, current_user.get("id"))
            menu_items = filtered_menu.get("filtered_items", menu_items)
            
            # Add metadata about filtering
            metadata = {
                "original_count": len(filtered_menu.get("original_items", [])),
                "filtered_count": len(filtered_menu.get("filtered_items", [])),
                "items_to_avoid": [item.model_dump() if hasattr(item, 'model_dump') else item for item in filtered_menu.get("items_to_avoid", [])],
                "conditions": filtered_menu.get("conditions", [])
            }
        else:
            metadata = None
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Prepare response
        response_data = {
            "success": True,
            "menu_items": menu_items,
            "raw_text": raw_text,
            "processing_time_ms": processing_time_ms,
            "enhanced": enhanced,
            "cached": False,
            "metadata": metadata
        }
        
        # Cache the result
        if not current_user:
            await cache.set(request.image_url, response_data)
        
        # Optional: Save to database
        if current_user:
            supabase = SupabaseClient()
            await supabase.save_ocr_result(request.image_url, response_data)
        
        return OCRResponse(**response_data)
    
    except requests.RequestException as e:
        logger.error(f"Error downloading image: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to download image: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image: {str(e)}"
        )
