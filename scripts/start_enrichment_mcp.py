#!/usr/bin/env python3
"""
Start menu enrichment using MCP Supabase tools and Ollama.
This script processes dishes in batches and updates the database.
"""

import asyncio
import aiohttp
import json
import logging
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen3:8b"
BATCH_SIZE = 10
MIN_DELAY = 0.5

async def query_ollama(prompt: str) -> str:
    """Query Ollama for dish enrichment."""
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant that provides accurate information about food dishes, ingredients, dietary classifications, and cuisine similarities. Always respond with valid JSON."
            },
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 2000}
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=120)
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("message", {}).get("content", "")
            return ""

async def enrich_dish(dish_name: str, description: str = "") -> dict:
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
    "similar_mexican": [{{"dish": "dish name", "similarity": 85}}, {{"dish": "dish name", "similarity": 78}}],
    "similar_european": [{{"dish": "dish name", "similarity": 82}}, {{"dish": "dish name", "similarity": 75}}],
    "similar_south_american": [{{"dish": "dish name", "similarity": 80}}, {{"dish": "dish name", "similarity": 72}}]
}}"""
    
    response = await query_ollama(prompt)
    if not response:
        return {}
    
    try:
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        return json.loads(response.strip())
    except:
        return {}

# This script will be called by MCP tools
# The actual enrichment loop will be handled via MCP Supabase execute_sql
logger.info("✅ Ollama enrichment service ready")
logger.info("💡 Use MCP Supabase tools to fetch dishes and update database")
logger.info("💡 This script provides the enrichment logic")



