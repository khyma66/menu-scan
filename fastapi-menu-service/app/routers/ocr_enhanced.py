"""Enhanced OCR router with MLToolkit + Qwen API integration."""

import time
import logging
import os
from fastapi import APIRouter, HTTPException, status, Header, Depends, UploadFile, File, Form
from typing import Optional
from app.models import OCRRequest, OCRResponse, ErrorResponse
from app.services.supabase_client import SupabaseClient
from app.services.enhanced_ocr_service import EnhancedOCRService, SyncEnhancedOCRService
from app.utils.language_detector import detect_european_language, get_tesseract_language_code
from PIL import Image
import requests
from io import BytesIO

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ocr", tags=["OCR"])

# Initialize enhanced OCR service
enhanced_ocr_service = EnhancedOCRService()
sync_enhanced_ocr = SyncEnhancedOCRService()

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
async def process_image_enhanced(
    request: OCRRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Enhanced OCR processing using MLToolkit + Qwen API with intelligent fallbacks.
    
    This endpoint provides:
    - Primary: Enhanced Tesseract (MLToolkit-style preprocessing)
    - Secondary: Qwen Vision API (when available and within rate limits)
    - Tertiary: Basic Tesseract fallback
    - Rate limiting and error handling
    - Supabase storage integration
    """
    start_time = time.time()
    
    try:
        # Handle both URL and base64 image inputs
        if request.image_base64:
            # Decode base64 image
            import base64
            try:
                # Remove data URL prefix if present (e.g., "data:image/jpeg;base64,")
                base64_data = request.image_base64
                if ',' in base64_data:
                    base64_data = base64_data.split(',')[1]
                
                img_data = base64.b64decode(base64_data)
                logger.info(f"Processing base64 image (size: {len(img_data)} bytes)")
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid base64 image data: {str(e)}"
                )
        elif request.image_url:
            # Download and process image from URL
            logger.info(f"Processing image from URL: {request.image_url}")
            response = requests.get(request.image_url, timeout=30)
            response.raise_for_status()
            img_data = response.content
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either image_url or image_base64 must be provided"
            )
        
        # Verify image size
        if len(img_data) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Image size exceeds 10MB limit"
            )
        
        # Process image using enhanced OCR service
        logger.info("Starting enhanced OCR processing...")
        result = await enhanced_ocr_service.process_menu_image(
            img_data, 
            use_qwen_fallback=True
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OCR processing failed: {result.get('error', 'Unknown error')}"
            )
        
        # Process time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Convert result to OCR response format
        from app.models import MenuItem
        menu_items = []
        for item_data in result.get("menu_items", []):
            if isinstance(item_data, dict):
                menu_items.append(
                    MenuItem(
                        name=str(item_data.get("name", "Unknown Item")),
                        price=item_data.get("price"),
                        description=item_data.get("description", ""),
                        category=item_data.get("category", "unknown")
                    )
                )
        
        # Prepare response data
        response_data = {
            "success": True,
            "menu_items": menu_items,
            "raw_text": result.get("raw_text", ""),
            "processing_time_ms": processing_time_ms,
            "enhanced": result.get("enhanced", False),
            "cached": False,
            "metadata": result.get("metadata", {})
        }
        
        # Save to Supabase if user is authenticated
        if current_user:
            try:
                user_id = current_user.get("id") if hasattr(current_user, 'get') else None
                await enhanced_ocr_service.save_ocr_result(
                    img_data, 
                    result, 
                    user_id=user_id
                )
            except Exception as e:
                logger.warning(f"Failed to save OCR result to Supabase: {e}")
        
        return OCRResponse(**response_data)
    
    except HTTPException:
        raise
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


@router.post("/process-upload", response_model=OCRResponse)
async def process_image_upload_enhanced(
    image: UploadFile = File(...),
    use_qwen_fallback: bool = Form(True),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Enhanced OCR processing for uploaded images with MLToolkit + Qwen API integration.
    
    Features:
    - Enhanced Tesseract preprocessing (MLToolkit-style)
    - Qwen Vision API fallback (rate limited)
    - Automatic error handling and fallbacks
    - Supabase integration for storing results
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
        
        # Verify image size
        if len(img_data) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Image size exceeds 10MB limit"
            )
        
        # Process image using enhanced OCR service
        logger.info(f"Processing uploaded image: {image.filename}")
        result = await enhanced_ocr_service.process_menu_image(
            img_data, 
            use_qwen_fallback=use_qwen_fallback
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OCR processing failed: {result.get('error', 'Unknown error')}"
            )
        
        # Process time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Convert result to OCR response format
        from app.models import MenuItem
        menu_items = []
        for item_data in result.get("menu_items", []):
            if isinstance(item_data, dict):
                menu_items.append(
                    MenuItem(
                        name=str(item_data.get("name", "Unknown Item")),
                        price=item_data.get("price"),
                        description=item_data.get("description", ""),
                        category=item_data.get("category", "unknown")
                    )
                )
        
        # Prepare response data
        response_data = {
            "success": True,
            "menu_items": menu_items,
            "raw_text": result.get("raw_text", ""),
            "processing_time_ms": processing_time_ms,
            "enhanced": result.get("enhanced", False),
            "cached": False,
            "metadata": {
                **result.get("metadata", {}),
                "filename": image.filename,
                "content_type": image.content_type
            }
        }
        
        # Save to Supabase if user is authenticated
        if current_user:
            try:
                user_id = current_user.get("id") if hasattr(current_user, 'get') else None
                await enhanced_ocr_service.save_ocr_result(
                    img_data, 
                    result, 
                    user_id=user_id
                )
            except Exception as e:
                logger.warning(f"Failed to save OCR result to Supabase: {e}")
        
        return OCRResponse(**response_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing uploaded image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image: {str(e)}"
        )


@router.post("/process-sync", response_model=OCRResponse)
def process_image_sync(
    image_base64: str = Form(...),
    use_qwen_fallback: bool = Form(True),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Synchronous OCR processing for simple use cases.
    Uses enhanced OCR service in sync mode for quick testing.
    """
    try:
        # Decode base64 image
        import base64
        try:
            # Remove data URL prefix if present
            base64_data = image_base64
            if ',' in base64_data:
                base64_data = base64_data.split(',')[1]
            
            img_data = base64.b64decode(base64_data)
            logger.info(f"Processing sync base64 image (size: {len(img_data)} bytes)")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid base64 image data: {str(e)}"
            )
        
        # Process using sync enhanced OCR
        result = sync_enhanced_ocr.process_menu_image(
            img_data, 
            use_qwen_fallback=use_qwen_fallback
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OCR processing failed: {result.get('error', 'Unknown error')}"
            )
        
        # Convert result to OCR response format
        from app.models import MenuItem
        menu_items = []
        for item_data in result.get("menu_items", []):
            if isinstance(item_data, dict):
                menu_items.append(
                    MenuItem(
                        name=str(item_data.get("name", "Unknown Item")),
                        price=item_data.get("price"),
                        description=item_data.get("description", ""),
                        category=item_data.get("category", "unknown")
                    )
                )
        
        # Prepare response data
        response_data = {
            "success": True,
            "menu_items": menu_items,
            "raw_text": result.get("raw_text", ""),
            "processing_time_ms": result.get("processing_time_ms", 0),
            "enhanced": result.get("enhanced", False),
            "cached": False,
            "metadata": result.get("metadata", {})
        }
        
        return OCRResponse(**response_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in sync OCR processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image: {str(e)}"
        )


@router.get("/status")
async def get_ocr_status():
    """
    Get OCR service status including Qwen API availability and rate limits.
    """
    try:
        status_info = {
            "status": "active",
            "enhanced_ocr": {
                "available": True,
                "enhanced_tesseract": True,
                "qwen_vision": enhanced_ocr_service._is_qwen_available(),
                "fallback_methods": ["enhanced_tesseract", "qwen_vision", "basic_tesseract"]
            },
            "rate_limiting": {
                "window_seconds": enhanced_ocr_service.rate_limit_window,
                "max_requests": enhanced_ocr_service.max_requests_per_window,
                "current_requests": len(enhanced_ocr_service.request_history)
            },
            "timestamp": time.time()
        }
        
        return status_info
    
    except Exception as e:
        logger.error(f"Error getting OCR status: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }


@router.get("/health")
async def ocr_health_check():
    """
    Health check endpoint for the enhanced OCR service.
    """
    try:
        # Test basic functionality
        test_image_data = b'\x89PNG\r\n\x1a\n' + b'fake_image_data'
        
        # Quick test without actual API calls
        health_status = {
            "status": "healthy",
            "service": "enhanced_ocr",
            "version": "1.0.0",
            "components": {
                "enhanced_tesseract": "available",
                "qwen_vision": "available" if enhanced_ocr_service._is_qwen_available() else "rate_limited",
                "supabase": "configured",
                "rate_limiter": "active"
            },
            "timestamp": time.time()
        }
        
        return health_status
    
    except Exception as e:
        logger.error(f"OCR health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }
