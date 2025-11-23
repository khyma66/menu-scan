"""Ollama Qwen model service for dish enrichment."""

import asyncio
import time
import logging
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class OllamaQwenService:
    """Service for querying Qwen model via local Ollama API."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen3:8b"):
        """
        Initialize Ollama Qwen service.
        
        Args:
            base_url: Ollama API base URL (default: http://localhost:11434)
            model: Model name (default: qwen3:8b)
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.chat_endpoint = f"{self.base_url}/api/chat"
        self.generate_endpoint = f"{self.base_url}/api/generate"
        
        # Minimal rate limiting for local Ollama (to avoid overwhelming)
        self.min_delay_between_requests = 0.5  # 0.5 seconds between requests (local is fast)
        self.last_request_time = 0
        
        logger.info(f"Initialized Ollama Qwen service: {self.base_url}, model: {self.model}")
        
    async def _wait_for_rate_limit(self):
        """Wait if necessary to avoid overwhelming local Ollama."""
        current_time = time.time()
        
        # Enforce minimum delay between requests (local Ollama can handle more, but be gentle)
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_delay_between_requests:
            wait_time = self.min_delay_between_requests - time_since_last
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    async def _query_qwen(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """Query Qwen model via Ollama API."""
        await self._wait_for_rate_limit()
        
        headers = {
            "Content-Type": "application/json",
        }
        
        # Ollama chat API format
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that provides accurate information about food dishes, ingredients, dietary classifications, and cuisine similarities. Always respond with valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 2000
            }
        }
        
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.chat_endpoint,
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=120)  # Longer timeout for local processing
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            # Ollama returns message.content directly
                            content = data.get("message", {}).get("content", "")
                            if not content:
                                # Try alternative format
                                content = data.get("response", "")
                            logger.info(f"Ollama Qwen API call successful")
                            return content
                        else:
                            error_text = await response.text()
                            logger.error(f"Ollama API error {response.status}: {error_text}")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(2)
                                continue
                            return None
            except asyncio.TimeoutError:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    continue
            except aiohttp.ClientError as e:
                logger.error(f"Connection error querying Ollama: {e}")
                if attempt < max_retries - 1:
                    logger.warning("Make sure Ollama is running: ollama serve")
                    await asyncio.sleep(5)
                    continue
            except Exception as e:
                logger.error(f"Error querying Ollama Qwen: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    continue
        
        return None
    
    async def enrich_dish(self, dish_name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Enrich a dish with ingredients, dietary classification, and similar dishes.
        
        Returns:
            {
                "ingredients": ["ingredient1", "ingredient2", ...],
                "vegetarian": true/false,
                "vegan": true/false,
                "non_vegetarian": true/false,
                "similar_mexican": [
                    {"dish": "dish_name", "similarity": 85},
                    {"dish": "dish_name", "similarity": 78}
                ],
                "similar_european": [
                    {"dish": "dish_name", "similarity": 82},
                    {"dish": "dish_name", "similarity": 75}
                ],
                "similar_south_american": [
                    {"dish": "dish_name", "similarity": 80},
                    {"dish": "dish_name", "similarity": 72}
                ]
            }
        """
        prompt = f"""Analyze this dish and provide detailed information in JSON format:

Dish Name: {dish_name}
Description: {description or "Not provided"}

Please provide:
1. Complete list of ingredients (as array of strings)
2. Dietary classification:
   - vegetarian: true if no meat/fish, false otherwise
   - vegan: true if no animal products, false otherwise
   - non_vegetarian: true if contains meat/fish, false otherwise
3. Top 2 similar dishes from Mexican cuisine with similarity percentage (0-100)
4. Top 2 similar dishes from European cuisine (any country) with similarity percentage
5. Top 2 similar dishes from South American cuisine with similarity percentage

Return ONLY valid JSON in this exact format:
{{
    "ingredients": ["ingredient1", "ingredient2", ...],
    "vegetarian": true/false,
    "vegan": true/false,
    "non_vegetarian": true/false,
    "similar_mexican": [
        {{"dish": "dish name", "similarity": 85}},
        {{"dish": "dish name", "similarity": 78}}
    ],
    "similar_european": [
        {{"dish": "dish name", "similarity": 82}},
        {{"dish": "dish name", "similarity": 75}}
    ],
    "similar_south_american": [
        {{"dish": "dish name", "similarity": 80}},
        {{"dish": "dish name", "similarity": 72}}
    ]
}}"""
        
        response = await self._query_qwen(prompt)
        if not response:
            return {}
        
        try:
            # Extract JSON from response (might have markdown formatting)
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            data = json.loads(response)
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Qwen response as JSON: {e}")
            logger.error(f"Response was: {response[:500]}")
            return {}
    
    async def batch_enrich_dishes(self, dishes: List[Dict[str, Any]], batch_size: int = 10) -> List[Dict[str, Any]]:
        """
        Enrich multiple dishes with minimal rate limiting (local Ollama is fast).
        
        Args:
            dishes: List of dicts with 'dish_name' and optional 'description'
            batch_size: Number of dishes to process before brief pause
        
        Returns:
            List of enrichment results
        """
        results = []
        total = len(dishes)
        
        for i, dish in enumerate(dishes):
            logger.info(f"Processing dish {i+1}/{total}: {dish.get('dish_name', 'Unknown')}")
            
            result = await self.enrich_dish(
                dish.get("dish_name", ""),
                dish.get("description")
            )
            
            result["dish_name"] = dish.get("dish_name")
            results.append(result)
            
            # Brief pause after each batch (local Ollama can handle more)
            if (i + 1) % batch_size == 0 and i + 1 < total:
                logger.info(f"Completed batch. Brief pause...")
                await asyncio.sleep(2)  # Much shorter pause for local
        
        return results
    
    async def check_ollama_available(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            async with aiohttp.ClientSession() as session:
                # Check if Ollama is running
                async with session.get(
                    f"{self.base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [m.get("name", "") for m in data.get("models", [])]
                        if self.model in models:
                            logger.info(f"✅ Ollama is running and model {self.model} is available")
                            return True
                        else:
                            logger.warning(f"⚠️ Ollama is running but model {self.model} not found. Available models: {models}")
                            logger.warning(f"💡 Run: ollama pull {self.model}")
                            return False
                    return False
        except Exception as e:
            logger.error(f"❌ Ollama is not available: {e}")
            logger.error(f"💡 Start Ollama: ollama serve")
            return False

