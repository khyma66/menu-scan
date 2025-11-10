"""Qwen Table Extraction Service using Together AI API."""

import httpx
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class QwenTableExtractor:
    """Service for extracting table data from text using Qwen models via Together AI."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "Qwen/Qwen2.5-Coder-32B-Instruct"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def extract_table_data(
        self,
        text: str,
        table_format: str = "markdown",
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Extract table data from text using Qwen model.

        Args:
            text: Input text containing table data
            table_format: Output format ('markdown', 'json', 'csv', 'html')
            max_tokens: Maximum tokens for response

        Returns:
            Dict containing extracted table data and metadata
        """
        try:
            prompt = self._build_extraction_prompt(text, table_format)

            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": max_tokens,
                    "stream": False
                }
            )

            response.raise_for_status()
            result = response.json()

            table_content = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})

            logger.info(f"Table extraction completed. Tokens used: {usage.get('total_tokens', 0)}")

            return {
                "success": True,
                "raw_table": table_content.strip(),
                "format": table_format,
                "model_used": self.model,
                "tokens_used": usage.get("total_tokens", 0),
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "processing_time_ms": None,  # Could be calculated if needed
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error extracting table data: {e}")
            return {
                "success": False,
                "error": str(e),
                "raw_table": "",
                "format": table_format,
                "model_used": self.model,
                "tokens_used": 0,
                "timestamp": datetime.utcnow().isoformat()
            }

    def _build_extraction_prompt(self, text: str, table_format: str) -> str:
        """Build the extraction prompt for the Qwen model."""
        return f"""
Extract all tabular data from the following text and format it as {table_format}.

IMPORTANT INSTRUCTIONS:
1. Look for any tables, lists, structured data, or key-value pairs
2. Convert them to clean {table_format} format
3. Use appropriate column headers
4. Maintain data accuracy and structure
5. If no tabular data is found, create a summary table
6. Return ONLY the formatted table, no additional text or explanations

TEXT TO PROCESS:
{text}

OUTPUT FORMAT: {table_format}
"""

    async def extract_tables_from_image_ocr(
        self,
        ocr_text: str,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract tables specifically from OCR text of images.
        Optimized for menu/document OCR results.
        """
        enhanced_prompt = f"""
You are processing OCR text from an image. Extract all menu items, tables, or structured data.

OCR TEXT:
{ocr_text}

INSTRUCTIONS:
- Identify menu items, prices, categories
- Extract tabular data (ingredients, nutritional info, etc.)
- Create structured tables in markdown format
- Group related items together
- Clean up OCR artifacts (spacing, line breaks)
- Return only the formatted tables
"""

        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": enhanced_prompt}],
                    "temperature": 0.1,
                    "max_tokens": 3000,
                }
            )

            response.raise_for_status()
            result = response.json()

            table_content = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})

            return {
                "success": True,
                "raw_table": table_content.strip(),
                "format": "markdown",
                "model_used": self.model,
                "tokens_used": usage.get("total_tokens", 0),
                "source": "ocr_image",
                "image_url": image_url,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error extracting tables from OCR: {e}")
            return {
                "success": False,
                "error": str(e),
                "raw_table": "",
                "format": "markdown",
                "model_used": self.model,
                "tokens_used": 0,
                "source": "ocr_image",
                "timestamp": datetime.utcnow().isoformat()
            }


# Synchronous version for backward compatibility
class SyncQwenTableExtractor:
    """Synchronous version of QwenTableExtractor for simpler use cases."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "Qwen/Qwen2.5-Coder-32B-Instruct"

    def extract_table_data(self, text: str, table_format: str = "markdown") -> Dict[str, Any]:
        """Synchronous table extraction."""
        import requests

        try:
            prompt = self._build_extraction_prompt(text, table_format)

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 2000,
                },
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            table_content = result["choices"][0]["message"]["content"]

            return {
                "success": True,
                "raw_table": table_content.strip(),
                "format": table_format,
                "model_used": self.model,
                "tokens_used": result.get("usage", {}).get("total_tokens", 0),
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error in sync table extraction: {e}")
            return {
                "success": False,
                "error": str(e),
                "raw_table": "",
                "format": table_format,
                "model_used": self.model,
                "tokens_used": 0,
                "timestamp": datetime.utcnow().isoformat()
            }

    def _build_extraction_prompt(self, text: str, table_format: str) -> str:
        """Build the extraction prompt for the Qwen model."""
        return f"""
Extract all tabular data from the following text and format it as {table_format}.

IMPORTANT INSTRUCTIONS:
1. Look for any tables, lists, structured data, or key-value pairs
2. Convert them to clean {table_format} format
3. Use appropriate column headers
4. Maintain data accuracy and structure
5. If no tabular data is found, create a summary table
6. Return ONLY the formatted table, no additional text or explanations

TEXT TO PROCESS:
{text}

OUTPUT FORMAT: {table_format}
"""