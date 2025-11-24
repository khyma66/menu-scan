"""OCR router for processing menu images."""

import time
import logging
import os
from fastapi import APIRouter, HTTPException, status, Header, Depends, UploadFile, File, Form
from typing import Optional
from app.models import OCRRequest, OCRResponse, ErrorResponse
# Redis cache disabled for performance - comment out to skip
# from app.services.redis_cache import RedisCache
from app.services.supabase_client import SupabaseClient
from app.services.llm_fallback import LLMFallback
from app.services.qwen_vision_service import QwenVisionService
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

# Set up Tesseract environment at module level
TESSDATA_PREFIX = "/usr/share/tesseract-ocr/5/tessdata"
TESSERACT_CMD = "/usr/bin/tesseract"

# Configure Tesseract environment
os.environ['TESSDATA_PREFIX'] = TESSDATA_PREFIX
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

logger.info(f"Tesseract environment configured at module level: TESSDATA_PREFIX={TESSDATA_PREFIX}, tesseract_cmd={TESSERACT_CMD}")


def setup_tesseract_environment():
    """Set up Tesseract environment variables for proper OCR functionality."""
    # Ensure environment is set (redundant but safe)
    os.environ['TESSDATA_PREFIX'] = TESSDATA_PREFIX
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    
    logger.info(f"Tesseract environment verified: TESSDATA_PREFIX={TESSDATA_PREFIX}, tesseract_cmd={TESSERACT_CMD}")


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
    Process a menu image from URL or base64 and extract menu items.
    
    Optionally filters results based on user's health conditions if authenticated.
    """
    # Set up Tesseract environment
    setup_tesseract_environment()
    
    start_time = time.time()
    
    try:
        # Skip cache for now (Redis is optional) - improves speed
        # Cache check removed to speed up processing
        
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
        
        # Process image with Tesseract OCR
        image = Image.open(BytesIO(img_data))
        
        # Set language for OCR
        ocr_language = request.language if request.language != "auto" else "eng"
        raw_text = pytesseract.image_to_string(image, lang=ocr_language)
        
        if not raw_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No text detected in image"
            )
        
        # Auto-detect language if requested
        detected_lang = request.language
        if request.language == "auto":
            detected_lang = detect_european_language(raw_text)
            logger.info(f"Auto-detected language: {detected_lang}")
            # Re-run OCR with detected language for better accuracy
            if detected_lang != "en":
                tesseract_lang = get_tesseract_language_code(detected_lang)
                try:
                    raw_text = pytesseract.image_to_string(image, lang=tesseract_lang)
                    logger.info(f"Re-ran OCR with language: {tesseract_lang}")
                except Exception as e:
                    logger.warning(f"Failed to use detected language {tesseract_lang}, using English: {e}")
                    raw_text = pytesseract.image_to_string(image, lang="eng")
        
        # Extract menu items from raw text
        menu_items = extract_menu_items(raw_text)
        
        # Use LLM enhancement if requested (disabled by default for speed)
        enhanced = False
        qwen_used = False
        if request.use_llm_enhancement:
            logger.info("LLM enhancement requested - this will slow down processing")
            llm_service = LLMFallback()
            llm_result = await llm_service.enhance_ocr_result(raw_text, detected_lang)

            if llm_result.get("enhanced"):
                menu_items = llm_result.get("menu_items", menu_items)
                enhanced = True
        
        # Skip translation for now to speed up processing
        translated_items = []
        for item in menu_items:
            if isinstance(item, dict):
                item_copy = item.copy()
                item_copy["original_name"] = item.get("name", "")
                translated_items.append(item_copy)
            else:
                # Handle MenuItem objects
                translated_items.append({
                    "name": getattr(item, "name", ""),
                    "price": getattr(item, "price", None),
                    "description": getattr(item, "description", None),
                    "category": getattr(item, "category", None),
                    "original_name": getattr(item, "name", "")
                })
        
        # Convert back to MenuItem objects with English names
        from app.models import MenuItem
        menu_items = []
        for item in translated_items:
            try:
                # Ensure item is a dict and has required fields
                if isinstance(item, dict):
                    name = item.get("name", "")
                    price = item.get("price")
                    description = item.get("description")
                    category = item.get("category")
                else:
                    # Handle case where item might be an object
                    name = getattr(item, "name", "")
                    price = getattr(item, "price", None)
                    description = getattr(item, "description", None)
                    category = getattr(item, "category", None)

                menu_items.append(
                    MenuItem(
                        name=str(name),  # Ensure it's a string
                        price=price,
                        description=description,
                        category=category
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to create MenuItem from {item}: {e}")
                # Create a basic MenuItem if conversion fails
                menu_items.append(
                    MenuItem(
                        name="Unknown Item",
                        price=None,
                        description=None,
                        category=None
                    )
                )
        
        # Enhanced metadata
        metadata = {
            "detected_language": detected_lang,
            "translated": True,
            "qwen_vl_max_used": qwen_used,
            "llm_enhanced": enhanced and not qwen_used,
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
            # Convert MenuItem objects to dicts for JSON serialization
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
            await supabase.save_ocr_result(request.image_url, serializable_data)
        
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


@router.post("/translate", response_model=OCRResponse)
async def translate_ocr_result(
    raw_text: str = Form(...),
    detected_language: str = Form("auto"),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Translate OCR text to English using the translation service.
    """
    start_time = time.time()

    try:
        # Extract menu items from raw text
        menu_items = extract_menu_items(raw_text)

        # Translate menu items to English using dish database
        from app.services.translation_service import TranslationService
        translation_service = TranslationService()

        # Convert MenuItem objects to dicts for translation
        menu_items_dict = []
        for item in menu_items:
            if isinstance(item, dict):
                menu_items_dict.append(item)
            else:
                # Handle MenuItem objects
                menu_items_dict.append({
                    "name": getattr(item, "name", ""),
                    "price": getattr(item, "price", None),
                    "description": getattr(item, "description", None),
                    "category": getattr(item, "category", None)
                })

        # Translate to English and save translations to database
        user_id = current_user.get("id") if current_user and hasattr(current_user, 'get') else None
        try:
            translated_items = await translation_service.translate_menu_items(
                menu_items_dict,
                detected_language=detected_language,
                user_id=user_id
            )
        except Exception as e:
            logger.warning(f"Translation service failed: {e}, using original items")
            # If translation fails, just add original_name to items
            translated_items = []
            for item in menu_items_dict:
                item_copy = item.copy()
                item_copy["original_name"] = item.get("name", "")
                translated_items.append(item_copy)

        # Convert back to MenuItem objects with English names
        from app.models import MenuItem
        menu_items = []
        for item in translated_items:
            try:
                # Ensure item is a dict and has required fields
                if isinstance(item, dict):
                    name = item.get("name", "")
                    price = item.get("price")
                    description = item.get("description")
                    category = item.get("category")
                else:
                    # Handle case where item might be an object
                    name = getattr(item, "name", "")
                    price = getattr(item, "price", None)
                    description = getattr(item, "description", None)
                    category = getattr(item, "category", None)

                menu_items.append(
                    MenuItem(
                        name=str(name),  # Ensure it's a string
                        price=price,
                        description=description,
                        category=category
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to create MenuItem from {item}: {e}")
                # Create a basic MenuItem if conversion fails
                menu_items.append(
                    MenuItem(
                        name="Unknown Item",
                        price=None,
                        description=None,
                        category=None
                    )
                )

        # Metadata for translation
        metadata = {
            "detected_language": detected_language,
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
            "enhanced": False,
            "cached": False,
            "metadata": metadata
        }

        return OCRResponse(**response_data)

    except Exception as e:
        logger.error(f"Error translating OCR result: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error translating OCR result: {str(e)}"
        )


@router.post("/process-upload", response_model=OCRResponse)
async def process_image_upload(
    image: UploadFile = File(...),
    use_llm_enhancement: bool = Form(True),
    use_qwen_vision: bool = Form(False),  # New parameter for Qwen vision
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

        # Use Qwen Vision if requested (direct image processing)
        enhanced = False
        qwen_used = False
        if use_qwen_vision:
            logger.info("Qwen-VL-Max Vision processing requested")
            try:
                qwen_service = QwenVisionService()
                qwen_result = await qwen_service.process_menu_image(img_data)

                if qwen_result.get("menu_items") and len(qwen_result["menu_items"]) > 0:
                    # Convert Qwen result to menu items format
                    menu_items = []
                    for item in qwen_result["menu_items"]:
                        from app.models import MenuItem
                        menu_items.append(MenuItem(
                            name=item.get("name", "Unknown"),
                            price=item.get("price"),
                            description=item.get("description"),
                            category=item.get("category", "unknown")
                        ))
                    enhanced = True
                    qwen_used = True
                    logger.info(f"Qwen-VL-Max Vision extracted {len(menu_items)} items")
                else:
                    logger.warning("Qwen-VL-Max Vision processing failed, falling back to OCR")
            except Exception as e:
                logger.error(f"Qwen-VL-Max Vision processing error: {e}, falling back to OCR")

        # Use LLM enhancement if requested (disabled by default for speed)
        if not qwen_used and use_llm_enhancement:
            logger.info("LLM enhancement requested - this will slow down processing")
            llm_service = LLMFallback()
            llm_result = await llm_service.enhance_ocr_result(raw_text, detected_lang)

            if llm_result.get("enhanced"):
                menu_items = llm_result.get("menu_items", menu_items)
                enhanced = True
        
        # Skip translation for now to speed up processing
        translated_items = []
        for item in menu_items:
            if isinstance(item, dict):
                item_copy = item.copy()
                item_copy["original_name"] = item.get("name", "")
                translated_items.append(item_copy)
            else:
                # Handle MenuItem objects
                translated_items.append({
                    "name": getattr(item, "name", ""),
                    "price": getattr(item, "price", None),
                    "description": getattr(item, "description", None),
                    "category": getattr(item, "category", None),
                    "original_name": getattr(item, "name", "")
                })
        
        # Convert back to MenuItem objects with English names
        from app.models import MenuItem
        menu_items = []
        for item in translated_items:
            try:
                # Ensure item is a dict and has required fields
                if isinstance(item, dict):
                    name = item.get("name", "")
                    price = item.get("price")
                    description = item.get("description")
                    category = item.get("category")
                else:
                    # Handle case where item might be an object
                    name = getattr(item, "name", "")
                    price = getattr(item, "price", None)
                    description = getattr(item, "description", None)
                    category = getattr(item, "category", None)

                menu_items.append(
                    MenuItem(
                        name=str(name),  # Ensure it's a string
                        price=price,
                        description=description,
                        category=category
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to create MenuItem from {item}: {e}")
                # Create a basic MenuItem if conversion fails
                menu_items.append(
                    MenuItem(
                        name="Unknown Item",
                        price=None,
                        description=None,
                        category=None
                    )
                )
        
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
            # Convert MenuItem objects to dicts for JSON serialization
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
            await supabase.save_ocr_result(fake_url, serializable_data)
        
        return OCRResponse(**response_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing uploaded image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image: {str(e)}"
        )
