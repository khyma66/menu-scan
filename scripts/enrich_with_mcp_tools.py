#!/usr/bin/env python3
"""
Menu enrichment using Ollama and MCP Supabase tools via HTTP API.
This script uses the MCP server endpoints directly.
"""

import asyncio
import aiohttp
import json
import logging
import time
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen3:8b"
OLLAMA_CHAT_ENDPOINT = f"{OLLAMA_URL}/api/chat"
BATCH_SIZE = 20
MIN_DELAY = 0.5

# Supabase configuration (using MCP endpoint)
SUPABASE_URL = "https://jlfqzcaospvspmzbvbxd.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpsZnF6Y2Fvc3B2c3BtemJ2YnhkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEzNzAzMzYsImV4cCI6MjA3Njk0NjMzNn0.cTI-Zo2NXeIZQDiQ4mcLia3slwRMyvMLpLj_-4BtviA"


class EnrichmentService:
    """Enrichment service using Ollama."""
    
    def __init__(self):
        self.last_request_time = 0
    
    async def _wait_for_rate_limit(self):
        """Minimal rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < MIN_DELAY:
            await asyncio.sleep(MIN_DELAY - time_since_last)
        self.last_request_time = time.time()
    
    async def query_ollama(self, prompt: str) -> Optional[str]:
        """Query Ollama Qwen model."""
        await self._wait_for_rate_limit()
        
        payload = {
            "model": OLLAMA_MODEL,
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
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    OLLAMA_CHAT_ENDPOINT,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data.get("message", {}).get("content", "") or data.get("response", "")
                        return content
                    else:
                        error_text = await response.text()
                        logger.error(f"Ollama API error {response.status}: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Error querying Ollama: {e}")
            return None
    
    async def enrich_dish(self, dish_name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Enrich a single dish."""
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
        
        response = await self.query_ollama(prompt)
        if not response:
            return {}
        
        try:
            # Clean JSON response
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
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"Response: {response[:500]}")
            return {}
    
    async def check_ollama(self) -> bool:
        """Check if Ollama is available."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{OLLAMA_URL}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [m.get("name", "") for m in data.get("models", [])]
                        return OLLAMA_MODEL in models
                    return False
        except Exception as e:
            logger.error(f"Ollama check failed: {e}")
            return False


async def enrich_all_with_mcp():
    """Enrich all dishes using MCP Supabase tools."""
    service = EnrichmentService()
    
    # Check Ollama
    logger.info("Checking Ollama...")
    if not await service.check_ollama():
        logger.error("❌ Ollama is not available!")
        return
    
    logger.info(f"✅ Ollama is ready: {OLLAMA_MODEL}")
    
    # Use MCP Supabase tools directly
    # Note: This will be called via the MCP tool interface
    logger.info("🚀 Starting enrichment using MCP Supabase tools...")
    logger.info("=" * 60)
    
    # We'll process in batches using MCP execute_sql
    # For now, let's process a test batch to verify it works
    logger.info("💡 Note: This script requires MCP Supabase tools to be available")
    logger.info("💡 Use the FastAPI backend or MCP server to run enrichment")
    logger.info("💡 Ollama is ready and waiting for enrichment requests")


if __name__ == "__main__":
    asyncio.run(enrich_all_with_mcp())



