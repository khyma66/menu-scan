"""LLM fallback service for enhancing OCR results."""

import openai
import anthropic
from typing import Dict, Any, List
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class LLMFallback:
    """Service for using LLM to enhance OCR results."""
    
    def __init__(self):
        """Initialize LLM clients."""
        self.openai_client = None
        self.anthropic_client = None
        
        if settings.openai_api_key:
            openai.api_key = settings.openai_api_key
            self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        
        if settings.anthropic_api_key:
            self.anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    
    async def enhance_ocr_result(self, raw_text: str, language: str = "en") -> Dict[str, Any]:
        """Enhance OCR results using LLM."""
        if not settings.fallback_enabled:
            return {"enhanced": False, "reason": "LLM fallback disabled"}
        
        if not self.openai_client and not self.anthropic_client:
            logger.warning("No LLM API keys configured")
            return {"enhanced": False, "reason": "No API keys"}
        
        try:
            if self.openai_client:
                return await self._enhance_with_openai(raw_text, language)
            elif self.anthropic_client:
                return await self._enhance_with_anthropic(raw_text, language)
        except Exception as e:
            logger.error(f"Error enhancing with LLM: {e}")
            return {"enhanced": False, "error": str(e)}
    
    async def _enhance_with_openai(self, raw_text: str, language: str) -> Dict[str, Any]:
        """Enhance using OpenAI."""
        try:
            response = self.openai_client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that extracts menu items from OCR text. Parse the text and return a structured list of menu items with names, prices, descriptions, and categories."
                    },
                    {
                        "role": "user",
                        "content": f"Extract menu items from this OCR text:\n\n{raw_text}"
                    }
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content
            import json
            parsed_result = json.loads(result)
            return {"enhanced": True, "menu_items": parsed_result.get("menu_items", [])}
        
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return {"enhanced": False, "error": str(e)}
    
    async def _enhance_with_anthropic(self, raw_text: str, language: str) -> Dict[str, Any]:
        """Enhance using Anthropic Claude."""
        try:
            message = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=4096,
                system="You are a helpful assistant that extracts menu items from OCR text. Parse the text and return a structured list of menu items with names, prices, descriptions, and categories in JSON format.",
                messages=[
                    {
                        "role": "user",
                        "content": f"Extract menu items from this OCR text:\n\n{raw_text}"
                    }
                ]
            )
            
            result = message.content[0].text
            import json
            parsed_result = json.loads(result)
            return {"enhanced": True, "menu_items": parsed_result.get("menu_items", [])}
        
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return {"enhanced": False, "error": str(e)}

