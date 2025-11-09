"""
Qwen-VL-Max Vision API Service for menu OCR processing
Direct integration with Qwen's vision API for optimal performance and cost
"""

import os
import json
import base64
import httpx
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class QwenVisionService:
    """
    Service to interact with Qwen-VL-Max API for menu image processing
    """

    def __init__(self):
        # OpenRouter API configuration (free tier)
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "qwen/qwen2.5-vl-32b-instruct:free"  # Latest free Qwen vision model
        self.timeout = 60  # 60 seconds for vision processing

        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY not set - vision processing will fail")

    async def process_menu_image(self, image_data: bytes, custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Process menu image using Qwen-VL-Max API

        Args:
            image_data: Raw image bytes
            custom_prompt: Optional custom prompt for extraction

        Returns:
            Dict containing extracted menu data
        """
        try:
            if not self.api_key:
                return self._create_error_response("Qwen API key not configured")

            # Convert image to base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')

            # Default prompt for menu extraction
            if custom_prompt is None:
                custom_prompt = self._build_menu_extraction_prompt()

            # Prepare the request for OpenRouter API (OpenAI-compatible format)
            request_data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": custom_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_b64}"
                                }
                            }
                        ]
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 2000
            }

            # Make API call to OpenRouter
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://menu-ocr.com",  # Optional: for rankings
                        "X-Title": "Menu OCR Service"  # Optional: for rankings
                    },
                    json=request_data
                )

                response.raise_for_status()
                result = response.json()

                # Extract the response content (OpenAI-compatible format)
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    return self._process_qwen_response(content)
                else:
                    return self._create_error_response("Invalid API response format")

        except httpx.TimeoutException:
            logger.error("Qwen vision processing timed out")
            return self._create_error_response("Processing timeout - image too complex")

        except Exception as e:
            logger.error(f"Qwen vision processing failed: {e}")
            return self._create_error_response(str(e))

    def _build_menu_extraction_prompt(self) -> str:
        """Build the menu extraction prompt for Qwen vision model"""
        return """
        Analyze this menu/restaurant image and extract all menu items with complete details:

        1. Restaurant name and basic information (cuisine type, location if visible)
        2. All menu items with:
           - Exact item name
           - Price (if visible)
           - Category (appetizer, main course, dessert, drink, salad, soup, etc.)
           - Description (if available)
           - Key ingredients mentioned

        3. Menu sections/categories
        4. Any special notes, dietary information, or allergens mentioned

        Return as clean JSON format:
        {
            "restaurant": {
                "name": "Restaurant Name",
                "cuisine_type": "Italian/Mediterranean/Asian/etc",
                "location": "City, Country (if visible)"
            },
            "menu_items": [
                {
                    "name": "Exact Dish Name",
                    "price": 25.99,
                    "category": "main/appetizer/dessert/drink",
                    "description": "Brief description if available",
                    "ingredients": ["ingredient1", "ingredient2"],
                    "dietary_notes": ["vegetarian", "spicy", etc.]
                }
            ],
            "menu_sections": ["Appetizers", "Main Courses", "Desserts"],
            "special_notes": ["Any additional information visible"]
        }

        IMPORTANT:
        - Extract EVERY visible menu item
        - Be accurate with names and prices
        - Only include information actually visible in the image
        - Return only valid JSON, no additional text
        """

    def _process_qwen_response(self, content: Any) -> Dict[str, Any]:
        """Process and structure the Qwen API response"""
        try:
            # Handle different response formats
            if isinstance(content, str):
                # Try to parse JSON string
                try:
                    menu_data = json.loads(content.strip())
                except json.JSONDecodeError:
                    # If not JSON, create structured response from text
                    menu_data = self._parse_text_response(content)
            elif isinstance(content, dict):
                menu_data = content
            else:
                return self._create_error_response("Invalid response format from Qwen API")

            # Validate and enhance the response
            validated_data = self._validate_menu_data(menu_data)

            # Add metadata
            validated_data["processing_metadata"] = {
                "model": "qwen-vl-max",
                "provider": "openrouter_api",
                "processing_type": "vision_ocr",
                "timestamp": datetime.utcnow().isoformat(),
                "api_version": "1.0"
            }

            return validated_data

        except Exception as e:
            logger.error(f"Failed to process Qwen response: {e}")
            return self._create_error_response(f"Response processing failed: {str(e)}")

    def _parse_text_response(self, text_response: str) -> Dict[str, Any]:
        """Parse text response into structured menu data"""
        # Basic text parsing for fallback
        lines = [line.strip() for line in text_response.split('\n') if line.strip()]

        menu_items = []
        restaurant_name = "Unknown Restaurant"

        for line in lines:
            # Try to extract restaurant name
            if "restaurant" in line.lower() and len(line) < 50:
                restaurant_name = line
                continue

            # Try to extract menu items (basic pattern matching)
            if '$' in line or any(char.isdigit() for char in line):
                # Simple item extraction
                parts = line.split('$')
                if len(parts) == 2:
                    name = parts[0].strip()
                    try:
                        price = float(parts[1].split()[0])
                        menu_items.append({
                            "name": name,
                            "price": price,
                            "category": "unknown",
                            "ingredients": []
                        })
                    except (ValueError, IndexError):
                        menu_items.append({
                            "name": line,
                            "price": None,
                            "category": "unknown",
                            "ingredients": []
                        })

        return {
            "restaurant": {
                "name": restaurant_name,
                "cuisine_type": "Unknown"
            },
            "menu_items": menu_items[:20],  # Limit to 20 items
            "menu_sections": [],
            "extraction_method": "text_fallback"
        }

    def _validate_menu_data(self, menu_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean menu data structure"""
        validated = {
            "restaurant": menu_data.get("restaurant", {}),
            "menu_items": [],
            "menu_sections": menu_data.get("menu_sections", []),
            "special_notes": menu_data.get("special_notes", [])
        }

        # Validate restaurant info
        restaurant = validated["restaurant"]
        if not isinstance(restaurant, dict):
            restaurant = {}
        restaurant.setdefault("name", "Unknown Restaurant")
        restaurant.setdefault("cuisine_type", "Unknown")

        # Validate menu items
        items = menu_data.get("menu_items", [])
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    validated_item = {
                        "name": str(item.get("name", "Unknown Item")),
                        "price": item.get("price"),
                        "category": str(item.get("category", "unknown")),
                        "description": str(item.get("description", "")),
                        "ingredients": item.get("ingredients", []) if isinstance(item.get("ingredients"), list) else [],
                        "dietary_notes": item.get("dietary_notes", []) if isinstance(item.get("dietary_notes"), list) else []
                    }
                    validated["menu_items"].append(validated_item)

        return validated

    def _create_error_response(self, error: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "restaurant": {"name": "Error", "cuisine_type": "Unknown"},
            "menu_items": [],
            "menu_sections": [],
            "processing_metadata": {
                "error": error,
                "model": "qwen-vl-max",
                "provider": "qwen_api",
                "timestamp": datetime.utcnow().isoformat()
            }
        }

# Synchronous version for backward compatibility
class SyncQwenVisionService:
    """Synchronous version for simpler use cases"""

    def __init__(self):
        self.async_service = QwenVisionService()

    def process_menu_image(self, image_data: bytes, custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Synchronous wrapper for async method"""
        import asyncio

        try:
            # Create new event loop for sync usage
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.async_service.process_menu_image(image_data, custom_prompt)
            )
            loop.close()
            return result
        except Exception as e:
            return self.async_service._create_error_response(f"Sync processing failed: {str(e)}")