"""OCR router for processing menu images."""

import time
import logging
from fastapi import APIRouter, HTTPException, status, Header, Depends, UploadFile, File, Form
from typing import Optional
from app.models import OCRRequest, OCRResponse, ErrorResponse
# Redis cache disabled for performance - comment out to skip
# from app.services.redis_cache import RedisCache
from app.services.supabase_client import SupabaseClient
from app.services.llm_fallback import LLMFallback
# Health service removed - no longer filtering by health conditions
# from app.services.health_service import HealthService
from app.utils.ocr_parser import extract_menu_items
from app.utils.language_detector import detect_european_language, get_tesseract_language_code
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
    Process a menu image from URL and extract menu items.
    
    Optionally filters results based on user's health conditions if authenticated.
    """
    start_time = time.time()
    
    try:
        # Skip cache for now (Redis is optional) - improves speed
        # Cache check removed to speed up processing
        
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
        
        # Auto-detect language if requested
        if request.language == "auto":
            detected_lang = detect_european_language(raw_text)
            logger.info(f"Auto-detected language: {detected_lang}")
            # Re-run OCR with detected language for better accuracy
            if detected_lang != "en":
                raw_text = pytesseract.image_to_string(image, lang=get_tesseract_language_code(detected_lang))
        
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
        
        # Translate menu items to English using dish database and save to translations table
        from app.services.translation_service import TranslationService
        translation_service = TranslationService()
        
        # Convert MenuItem objects to dicts for translation
        menu_items_dict = [
            {
                "name": item.name,
                "price": item.price,
                "description": item.description,
                "category": item.category
            }
            for item in menu_items
        ]
        
        # Translate to English and save translations to database
        user_id = current_user.get("id") if current_user else None
        translated_items = await translation_service.translate_menu_items(
            menu_items_dict,
            detected_language=detected_lang,
            user_id=user_id
        )
        
        # Convert back to MenuItem objects with English names
        from app.models import MenuItem
        menu_items = [
            MenuItem(
                name=item.get("name"),  # English name
                price=item.get("price"),
                description=item.get("description"),
                category=item.get("category")
            )
            for item in translated_items
        ]
        
        # Simple metadata without health filtering
        metadata = {
            "detected_language": detected_lang,
            "translated": True,
            "translation_count": len([item for item in translated_items if item.get("name") != item.get("original_name", item.get("name"))])
        }
        
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
        
        # Cache disabled for faster processing (Redis optional)
        
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


@router.post("/process-upload", response_model=OCRResponse)
async def process_image_upload(
    image: UploadFile = File(...),
    use_llm_enhancement: bool = Form(True),
    language: str = Form("auto"),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Process a menu image from file upload and extract menu items.
    
    Supports automatic European language detection.
    Optionally filters results based on user's health conditions if authenticated.
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
        
        # Process image with Tesseract OCR
        image_obj = Image.open(BytesIO(img_data))
        
        # Initial OCR with English (or specified language)
        if language == "auto":
            # Start with English, then detect
            raw_text = pytesseract.image_to_string(image_obj, lang="eng")
            
            # Auto-detect language
            if raw_text.strip():
                detected_lang = detect_european_language(raw_text)
                logger.info(f"Auto-detected language: {detected_lang}")
                
                # Re-run OCR with detected language for better accuracy
                if detected_lang != "en":
                    tesseract_lang = get_tesseract_language_code(detected_lang)
                    try:
                        raw_text = pytesseract.image_to_string(image_obj, lang=tesseract_lang)
                        logger.info(f"Re-ran OCR with language: {tesseract_lang}")
                    except Exception as e:
                        logger.warning(f"Failed to use detected language {tesseract_lang}, using English: {e}")
                        raw_text = pytesseract.image_to_string(image_obj, lang="eng")
            else:
                detected_lang = "en"
        else:
            # Use specified language
            raw_text = pytesseract.image_to_string(image_obj, lang=language)
            detected_lang = language
        
        if not raw_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No text detected in image"
            )
        
        # Extract menu items from raw text
        menu_items = extract_menu_items(raw_text)
        
        # Use LLM enhancement if requested
        enhanced = False
        if use_llm_enhancement:
            llm_service = LLMFallback()
            llm_result = await llm_service.enhance_ocr_result(raw_text, detected_lang)
            
            if llm_result.get("enhanced"):
                menu_items = llm_result.get("menu_items", menu_items)
                enhanced = True
        
        # Translate menu items to English using dish database and save to translations table
        from app.services.translation_service import TranslationService
        translation_service = TranslationService()
        
        # Convert MenuItem objects to dicts for translation
        menu_items_dict = [
            {
                "name": item.name,
                "price": item.price,
                "description": item.description,
                "category": item.category
            }
            for item in menu_items
        ]
        
        # Translate to English and save translations to database
        user_id = current_user.get("id") if current_user else None
        translated_items = await translation_service.translate_menu_items(
            menu_items_dict,
            detected_language=detected_lang,
            user_id=user_id
        )
        
        # Convert back to MenuItem objects with English names
        from app.models import MenuItem
        menu_items = [
            MenuItem(
                name=item.get("name"),  # English name
                price=item.get("price"),
                description=item.get("description"),
                category=item.get("category")
            )
            for item in translated_items
        ]
        
        # Simple metadata without health filtering
        metadata = {
            "detected_language": detected_lang,
            "translated": True,
            "translation_count": len([item for item in translated_items if item.get("name") != item.get("original_name", item.get("name"))])
        }
        
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
        
        # Optional: Save to database
        if current_user:
            supabase = SupabaseClient()
            # Create a fake URL for uploaded files
            fake_url = f"uploaded://{image.filename}"
            await supabase.save_ocr_result(fake_url, response_data)
        
        return OCRResponse(**response_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing uploaded image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image: {str(e)}"
        )
