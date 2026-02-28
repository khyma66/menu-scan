"""OCR router for processing menu images."""

import time
import logging
import os
from fastapi import APIRouter, HTTPException, status, Header, Depends, UploadFile, File, Form
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from app.models import OCRRequest, OCRResponse, ErrorResponse
# Redis cache disabled for performance - comment out to skip
# from app.services.redis_cache import RedisCache
from app.services.supabase_client import SupabaseClient
from app.services.llm_fallback import LLMFallback
from app.services.qwen_vision_service import QwenVisionService
from app.services.gemini_groq_menu_service import GeminiGroqMenuService
# Health service removed - no longer filtering by health conditions
# from app.services.health_service import HealthService
from app.utils.ocr_parser import extract_menu_items
from app.utils.language_detector import detect_european_language, get_tesseract_language_code
from PIL import Image
import requests
import pytesseract
from io import BytesIO

logger = logging.getLogger(__name__)

_HEALTH_PROFILE_CACHE: Dict[str, Dict[str, Any]] = {}
_HEALTH_PROFILE_CACHE_TTL_SECONDS = 120

async def _try_qwen_vision_fallback(img_data: bytes) -> Optional[OCRResponse]:
    """Try Qwen vision as fallback OCR method."""
    try:
        logger.info("Attempting Qwen vision OCR fallback")
        qwen_service = QwenVisionService()
        qwen_result = await qwen_service.process_menu_image(img_data)

        if qwen_result and qwen_result.get("menu_items") and len(qwen_result["menu_items"]) > 0:
            # Convert Qwen result to OCR response format
            menu_items = []
            for item in qwen_result["menu_items"]:
                from app.models import MenuItem
                # Convert price to string if it's a number
                price = item.get("price")
                if isinstance(price, (int, float)):
                    price = str(price)
                elif price is None:
                    price = None
                else:
                    price = str(price)

                menu_items.append(MenuItem(
                    name=item.get("name", "Unknown"),
                    price=price,
                    description=item.get("description"),
                    category=item.get("category", "unknown")
                ))

            # Create raw text from menu items
            raw_text_lines = []
            for item in qwen_result["menu_items"]:
                line = item.get("name", "Unknown")
                if item.get("price"):
                    line += f" ${item['price']}"
                raw_text_lines.append(line)
            raw_text = "\n".join(raw_text_lines)

            metadata = {
                "detected_language": "en",  # Qwen typically returns English
                "translated": False,
                "qwen_vl_max_used": True,
                "llm_enhanced": False,
                "translation_count": 0
            }

            response_data = {
                "success": True,
                "menu_items": menu_items,
                "raw_text": raw_text,
                "processing_time_ms": 1000,  # Estimate for vision processing
                "enhanced": True,
                "cached": False,
                "metadata": metadata
            }

            logger.info(f"Qwen vision extracted {len(menu_items)} items successfully")
            return OCRResponse(**response_data)
        else:
            logger.warning("Qwen vision returned no menu items")
            return None

    except Exception as e:
        logger.error(f"Qwen vision fallback failed: {e}")
        return None

router = APIRouter(prefix="/ocr", tags=["OCR"])


class MenuItemsTranslationRequest(BaseModel):
    menu_items: List[Dict[str, Any]]
    target_language: str


class MenuItemsTranslationResponse(BaseModel):
    menu_items: List[Dict[str, Any]]

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


def is_tesseract_available():
    """Check if Tesseract is available and working."""
    try:
        # Try to get tesseract version
        version = pytesseract.get_tesseract_version()
        logger.info(f"Tesseract version: {version}")
        return True
    except Exception as e:
        logger.warning(f"Tesseract not available: {e}")
        return False


    async def _try_qwen_vision_fallback(self, img_data: bytes) -> Optional[OCRResponse]:
        """Try Qwen vision as fallback OCR method."""
        try:
            logger.info("Attempting Qwen vision OCR fallback")
            qwen_service = QwenVisionService()
            qwen_result = await qwen_service.process_menu_image(img_data)

            if qwen_result and qwen_result.get("menu_items") and len(qwen_result["menu_items"]) > 0:
                # Convert Qwen result to OCR response format
                menu_items = []
                for item in qwen_result["menu_items"]:
                    from app.models import MenuItem
                    # Convert price to string if it's a number
                    price = item.get("price")
                    if isinstance(price, (int, float)):
                        price = str(price)
                    elif price is None:
                        price = None
                    else:
                        price = str(price)
    
                    menu_items.append(MenuItem(
                        name=item.get("name", "Unknown"),
                        price=price,
                        description=item.get("description"),
                        category=item.get("category", "unknown")
                    ))

                # Create raw text from menu items
                raw_text_lines = []
                for item in qwen_result["menu_items"]:
                    line = item.get("name", "Unknown")
                    if item.get("price"):
                        line += f" ${item['price']}"
                    raw_text_lines.append(line)
                raw_text = "\n".join(raw_text_lines)

                metadata = {
                    "detected_language": "en",  # Qwen typically returns English
                    "translated": False,
                    "qwen_vl_max_used": True,
                    "llm_enhanced": False,
                    "translation_count": 0
                }

                response_data = {
                    "success": True,
                    "menu_items": menu_items,
                    "raw_text": raw_text,
                    "processing_time_ms": 1000,  # Estimate for vision processing
                    "enhanced": True,
                    "cached": False,
                    "metadata": metadata
                }

                logger.info(f"Qwen vision extracted {len(menu_items)} items successfully")
                return OCRResponse(**response_data)
            else:
                logger.warning("Qwen vision returned no menu items")
                return None

        except Exception as e:
            logger.error(f"Qwen vision fallback failed: {e}")
            return None


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


async def _get_user_health_profile(user_id: Optional[str]) -> Dict[str, Any]:
    """Fetch health profile payload from existing health tables for recommendation prompts."""
    profile = {
        "health_conditions": [],
        "allergies": [],
        "dietary_preferences": [],
        "medical_notes": None,
    }
    if not user_id:
        return profile

    cache_entry = _HEALTH_PROFILE_CACHE.get(user_id)
    now = time.time()
    if cache_entry and (now - cache_entry.get("ts", 0) < _HEALTH_PROFILE_CACHE_TTL_SECONDS):
        cached_profile = cache_entry.get("profile")
        if isinstance(cached_profile, dict):
            return cached_profile

    try:
        supabase = SupabaseClient()
        if not supabase.client:
            return profile

        rows: List[Dict[str, Any]] = []

        # Preferred: normalized v2 health tables
        try:
            profile_row = supabase.client.table("health_profiles").select("id").eq("user_id", user_id).eq("is_active", True).limit(1).execute().data or []
            if profile_row:
                rows = supabase.client.table("health_conditions_v2").select("condition_type,condition_name,description").eq("profile_id", profile_row[0].get("id")).eq("is_active", True).execute().data or []
        except Exception:
            rows = []

        # Fallback: legacy condition rows
        if not rows:
            try:
                rows = supabase.client.table("health_conditions").select("condition_type,condition_name,description").eq("user_id", user_id).execute().data or []
            except Exception:
                rows = []

        # Fallback: compact array profile row
        if not rows:
            try:
                pref_rows = supabase.client.table("user_health_preferences").select("health_conditions,allergies,dietary_preferences,medical_notes").eq("user_id", user_id).limit(1).execute().data or []
                if pref_rows:
                    pref = pref_rows[0]
                    for name in pref.get("allergies") or []:
                        rows.append({"condition_type": "allergy", "condition_name": name, "description": None})
                    for name in pref.get("dietary_preferences") or []:
                        rows.append({"condition_type": "dietary", "condition_name": name, "description": None})
                    for name in pref.get("health_conditions") or []:
                        rows.append({"condition_type": "illness", "condition_name": name, "description": None})
                    if pref.get("medical_notes"):
                        rows.append({"condition_type": "illness", "condition_name": "medical-notes", "description": str(pref.get("medical_notes"))})
            except Exception:
                rows = rows

        notes = []
        for row in rows:
            condition_type = (row.get("condition_type") or "").lower()
            condition_name = row.get("condition_name")
            if not condition_name:
                continue
            if condition_type == "allergy":
                profile["allergies"].append(condition_name)
            elif condition_type == "dietary":
                profile["dietary_preferences"].append(condition_name)
            else:
                profile["health_conditions"].append(condition_name)

            if row.get("description"):
                notes.append(str(row.get("description")))

        if notes:
            profile["medical_notes"] = " | ".join(notes[:6])
    except Exception as exc:
        logger.warning("Health profile lookup failed for user=%s: %s", user_id, exc)

    _HEALTH_PROFILE_CACHE[user_id] = {"ts": now, "profile": profile}

    return profile


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

        # Check if Tesseract is available
        if is_tesseract_available():
            try:
                raw_text = pytesseract.image_to_string(image, lang=ocr_language)
            except Exception as e:
                logger.warning(f"Tesseract OCR failed: {e}, falling back to Qwen vision")
                # Try Qwen vision as fallback
                qwen_result = await _try_qwen_vision_fallback(img_data)
                if qwen_result:
                    return qwen_result
                else:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Both local OCR and Qwen OCR failed. Please retry.",
                    )
        else:
            logger.info("Tesseract not available, using Qwen vision OCR")
            # Try Qwen vision as primary OCR method
            qwen_result = await _try_qwen_vision_fallback(img_data)
            if qwen_result:
                return qwen_result
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Tesseract unavailable and Qwen OCR failed. Please retry.",
                )

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
            if detected_lang != "en" and is_tesseract_available():
                tesseract_lang = get_tesseract_language_code(detected_lang)
                try:
                    raw_text = pytesseract.image_to_string(image, lang=tesseract_lang)
                    logger.info(f"Re-ran OCR with language: {tesseract_lang}")
                except Exception as e:
                    logger.warning(f"Failed to use detected language {tesseract_lang}, keeping current text: {e}")
        
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
    output_language: str = Form("en"),
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
        
        user_id = current_user.get("id") if current_user and hasattr(current_user, "get") else None
        health_profile = await _get_user_health_profile(user_id)

        pipeline = GeminiGroqMenuService()
        detected_lang = "en" if language == "auto" else language
        enhanced = False

        raw_text = ""
        menu_items = []
        gemini_menu_items = []
        qwen_menu_items = []
        metadata = {}

        try:
            pipeline_result = await pipeline.process_menu(
                image_bytes=img_data,
                language_hint=language,
                health_profile=health_profile,
                use_groq_enhancement=use_llm_enhancement,
            )
            raw_text = pipeline_result.get("raw_text", "")
            metadata = pipeline_result.get("metadata", {})
            enhanced = metadata.get("pipeline") == "gemini_plus_groq"

            from app.models import MenuItem
            for item in pipeline_result.get("gemini_menu_items", []):
                gemini_menu_items.append(
                    MenuItem(
                        name=str(item.get("name") or "Unknown Item"),
                        price=item.get("price"),
                        description=item.get("description"),
                        category=item.get("category"),
                        ingredients=item.get("ingredients") if isinstance(item.get("ingredients"), list) else [],
                        taste=item.get("taste"),
                        similarDish1=item.get("similarDish1"),
                        similarDish2=item.get("similarDish2"),
                        recommendation=item.get("recommendation"),
                        recommendation_reason=item.get("recommendation_reason"),
                        allergens=item.get("allergens") if isinstance(item.get("allergens"), list) else [],
                        spiciness_level=item.get("spiciness_level"),
                        preparation_method=item.get("preparation_method"),
                    )
                )

            for item in pipeline_result.get("qwen_menu_items", []):
                qwen_menu_items.append(
                    MenuItem(
                        name=str(item.get("name") or "Unknown Item"),
                        price=item.get("price"),
                        description=item.get("description"),
                        category=item.get("category"),
                        ingredients=item.get("ingredients") if isinstance(item.get("ingredients"), list) else [],
                        taste=item.get("taste"),
                        similarDish1=item.get("similarDish1"),
                        similarDish2=item.get("similarDish2"),
                        recommendation=item.get("recommendation"),
                        recommendation_reason=item.get("recommendation_reason"),
                        allergens=item.get("allergens") if isinstance(item.get("allergens"), list) else [],
                        spiciness_level=item.get("spiciness_level"),
                        preparation_method=item.get("preparation_method"),
                    )
                )

            for item in pipeline_result.get("menu_items", []):
                menu_items.append(
                    MenuItem(
                        name=str(item.get("name") or "Unknown Item"),
                        price=item.get("price"),
                        description=item.get("description"),
                        category=item.get("category"),
                        ingredients=item.get("ingredients") if isinstance(item.get("ingredients"), list) else [],
                        taste=item.get("taste"),
                        similarDish1=item.get("similarDish1"),
                        similarDish2=item.get("similarDish2"),
                        recommendation=item.get("recommendation"),
                        recommendation_reason=item.get("recommendation_reason"),
                        allergens=item.get("allergens") if isinstance(item.get("allergens"), list) else [],
                        spiciness_level=item.get("spiciness_level"),
                        preparation_method=item.get("preparation_method"),
                    )
                )
        except Exception as llm_exc:
            logger.warning("Gemini/Groq pipeline failed, falling back to local OCR: %s", llm_exc)
            qwen_result = await _try_qwen_vision_fallback(img_data)
            if qwen_result:
                logger.info("Recovered OCR via Qwen vision fallback after Gemini/Groq failure")
                return qwen_result

            image_obj = Image.open(BytesIO(img_data))
            if is_tesseract_available():
                raw_text = pytesseract.image_to_string(image_obj, lang="eng")
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=(
                        "AI extraction failed and both Qwen fallback/local Tesseract OCR are unavailable on server. "
                        "Please retry shortly."
                    ),
                )

            if not raw_text.strip():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No text detected in image")

            extracted = extract_menu_items(raw_text)
            from app.models import MenuItem
            menu_items = [
                MenuItem(
                    name=str(item.get("name", "Unknown Item")),
                    price=item.get("price"),
                    description=item.get("description"),
                    category=item.get("category"),
                    ingredients=[],
                    taste=None,
                    similarDish1=None,
                    similarDish2=None,
                    recommendation=None,
                    recommendation_reason=None,
                    allergens=[],
                    spiciness_level=None,
                    preparation_method=None,
                )
                for item in extracted
            ]
            gemini_menu_items = list(menu_items)
            qwen_menu_items = list(menu_items)

            if not menu_items:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="No menu items could be extracted from image.",
                )

            metadata = {
                "pipeline": "fallback_tesseract",
                "ocr_model": None,
                "enhancement_model": None,
                "fallback_reason": str(llm_exc),
            }

        if output_language and output_language.lower() not in {"en", "english", "auto"}:
            try:
                source_menu_rows = [
                    {
                        "name": item.name,
                        "price": item.price,
                        "description": item.description,
                        "category": item.category,
                        "ingredients": item.ingredients,
                        "taste": item.taste,
                        "similarDish1": item.similarDish1,
                        "similarDish2": item.similarDish2,
                        "recommendation": item.recommendation,
                        "recommendation_reason": item.recommendation_reason,
                        "allergens": item.allergens,
                        "spiciness_level": item.spiciness_level,
                        "preparation_method": item.preparation_method,
                    }
                    for item in menu_items
                ]
                source_gemini_rows = [
                    {
                        "name": item.name,
                        "price": item.price,
                        "description": item.description,
                        "category": item.category,
                        "ingredients": item.ingredients,
                        "taste": item.taste,
                        "similarDish1": item.similarDish1,
                        "similarDish2": item.similarDish2,
                        "recommendation": item.recommendation,
                        "recommendation_reason": item.recommendation_reason,
                        "allergens": item.allergens,
                        "spiciness_level": item.spiciness_level,
                        "preparation_method": item.preparation_method,
                    }
                    for item in gemini_menu_items
                ]
                source_qwen_rows = [
                    {
                        "name": item.name,
                        "price": item.price,
                        "description": item.description,
                        "category": item.category,
                        "ingredients": item.ingredients,
                        "taste": item.taste,
                        "similarDish1": item.similarDish1,
                        "similarDish2": item.similarDish2,
                        "recommendation": item.recommendation,
                        "recommendation_reason": item.recommendation_reason,
                        "allergens": item.allergens,
                        "spiciness_level": item.spiciness_level,
                        "preparation_method": item.preparation_method,
                    }
                    for item in qwen_menu_items
                ]

                translated_rows = await pipeline.translate_menu_items(
                    menu_items=source_menu_rows,
                    target_language=output_language,
                )
                translated_gemini_rows = await pipeline.translate_menu_items(
                    menu_items=source_gemini_rows,
                    target_language=output_language,
                )
                translated_qwen_rows = await pipeline.translate_menu_items(
                    menu_items=source_qwen_rows,
                    target_language=output_language,
                )

                from app.models import MenuItem
                menu_items = [
                    MenuItem(
                        name=str(row.get("name") or "Unknown Item"),
                        price=row.get("price"),
                        description=row.get("description"),
                        category=row.get("category"),
                        ingredients=row.get("ingredients") if isinstance(row.get("ingredients"), list) else [],
                        taste=row.get("taste"),
                        similarDish1=row.get("similarDish1"),
                        similarDish2=row.get("similarDish2"),
                        recommendation=row.get("recommendation"),
                        recommendation_reason=row.get("recommendation_reason"),
                        allergens=row.get("allergens") if isinstance(row.get("allergens"), list) else [],
                        spiciness_level=row.get("spiciness_level"),
                        preparation_method=row.get("preparation_method"),
                    )
                    for row in translated_rows
                ]
                gemini_menu_items = [
                    MenuItem(
                        name=str(row.get("name") or "Unknown Item"),
                        price=row.get("price"),
                        description=row.get("description"),
                        category=row.get("category"),
                        ingredients=row.get("ingredients") if isinstance(row.get("ingredients"), list) else [],
                        taste=row.get("taste"),
                        similarDish1=row.get("similarDish1"),
                        similarDish2=row.get("similarDish2"),
                        recommendation=row.get("recommendation"),
                        recommendation_reason=row.get("recommendation_reason"),
                        allergens=row.get("allergens") if isinstance(row.get("allergens"), list) else [],
                        spiciness_level=row.get("spiciness_level"),
                        preparation_method=row.get("preparation_method"),
                    )
                    for row in translated_gemini_rows
                ]
                qwen_menu_items = [
                    MenuItem(
                        name=str(row.get("name") or "Unknown Item"),
                        price=row.get("price"),
                        description=row.get("description"),
                        category=row.get("category"),
                        ingredients=row.get("ingredients") if isinstance(row.get("ingredients"), list) else [],
                        taste=row.get("taste"),
                        similarDish1=row.get("similarDish1"),
                        similarDish2=row.get("similarDish2"),
                        recommendation=row.get("recommendation"),
                        recommendation_reason=row.get("recommendation_reason"),
                        allergens=row.get("allergens") if isinstance(row.get("allergens"), list) else [],
                        spiciness_level=row.get("spiciness_level"),
                        preparation_method=row.get("preparation_method"),
                    )
                    for row in translated_qwen_rows
                ]
                metadata["output_language"] = output_language
            except Exception as tr_exc:
                logger.warning("Output translation failed, keeping English rows: %s", tr_exc)

        if not menu_items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No menu items detected in image")

        metadata.update(
            {
                "detected_language": detected_lang,
                "translated": True,
                "health_profile_used": bool(user_id),
                "health_profile": health_profile,
            }
        )
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Prepare response
        response_data = {
            "success": True,
            "menu_items": menu_items,
            "gemini_menu_items": gemini_menu_items or list(menu_items),
            "qwen_menu_items": qwen_menu_items or list(menu_items),
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
                    "category": item.category,
                    "ingredients": item.ingredients,
                    "taste": item.taste,
                    "similarDish1": item.similarDish1,
                    "similarDish2": item.similarDish2,
                    "recommendation": item.recommendation,
                    "recommendation_reason": item.recommendation_reason,
                    "allergens": item.allergens,
                    "spiciness_level": item.spiciness_level,
                    "preparation_method": item.preparation_method,
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


@router.post("/translate-menu-items", response_model=MenuItemsTranslationResponse)
async def translate_menu_items(request: MenuItemsTranslationRequest):
    """Translate already-extracted menu rows to the requested language via Groq/Qwen."""
    try:
        pipeline = GeminiGroqMenuService()
        translated = await pipeline.translate_menu_items(
            menu_items=request.menu_items,
            target_language=request.target_language,
        )
        return MenuItemsTranslationResponse(menu_items=translated)
    except Exception as exc:
        logger.error("Failed to translate menu items, returning source rows: %s", exc)
        return MenuItemsTranslationResponse(menu_items=request.menu_items)
