#!/usr/bin/env python3
"""
Run enrichment in batches using MCP Supabase tools and Ollama.
This script processes batches autonomously with delays.
"""

import asyncio
import aiohttp
import json
import logging
import time
from typing import Dict, List, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler('enrichment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen3:8b"
BATCH_SIZE = 15
BATCH_DELAY = 3
MIN_DELAY = 0.5

last_request_time = 0
total_processed = 0
total_success = 0
total_failed = 0
start_time = time.time()


async def wait_for_rate_limit():
    """Minimal rate limiting."""
    global last_request_time
    current_time = time.time()
    time_since_last = current_time - last_request_time
    if time_since_last < MIN_DELAY:
        await asyncio.sleep(MIN_DELAY - time_since_last)
    last_request_time = time.time()


async def query_ollama(prompt: str) -> Optional[str]:
    """Query Ollama Qwen model."""
    await wait_for_rate_limit()
    
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
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{OLLAMA_URL}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=90)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("message", {}).get("content", "")
                return None
    except Exception as e:
        logger.error(f"Error querying Ollama: {e}")
        return None


async def enrich_dish(dish_name: str, ingredients: Optional[str] = None) -> Dict[str, Any]:
    """Enrich a single dish."""
    prompt = f"""Analyze this dish and provide detailed information in JSON format:

Dish Name: {dish_name}
Ingredients: {ingredients or "Not provided"}

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


def build_update_query(dish_name: str, enrichment: Dict[str, Any]) -> str:
    """Build SQL update query."""
    update_parts = []
    
    if enrichment.get("ingredients"):
        ingredients_str = ", ".join(enrichment["ingredients"])
        ingredients_escaped = ingredients_str.replace("'", "''")
        update_parts.append(f'"ingredients_complete" = \'{ingredients_escaped}\'')
    
    if "vegetarian" in enrichment:
        update_parts.append(f'"vegetarian_flag" = {str(enrichment["vegetarian"]).lower()}')
    if "vegan" in enrichment:
        update_parts.append(f'"vegan_flag" = {str(enrichment["vegan"]).lower()}')
    if "non_vegetarian" in enrichment:
        update_parts.append(f'"non_vegetarian_flag" = {str(enrichment["non_vegetarian"]).lower()}')
    
    for cuisine in ["mexican", "european", "south_american"]:
        key = f"similar_{cuisine}"
        if enrichment.get(key):
            dishes_list = enrichment[key]
            for i, similar_dish in enumerate(dishes_list[:2], 1):
                if similar_dish.get("dish"):
                    dish_name_escaped = similar_dish["dish"].replace("'", "''")
                    similarity = similar_dish.get("similarity", 0)
                    update_parts.append(f'"similar_{cuisine}_dish_{i}" = \'{dish_name_escaped}\'')
                    update_parts.append(f'"similar_{cuisine}_similarity_{i}" = {similarity}')
    
    if update_parts:
        update_parts.append('"enrichment_status" = \'completed\'')
        update_parts.append('"enrichment_updated_at" = NOW()')
        
        set_clause = ", ".join(update_parts)
        dish_name_escaped = dish_name.replace("'", "''")
        
        return f'''
            UPDATE public.menu
            SET {set_clause}
            WHERE "Dish Name" = '{dish_name_escaped}'
        '''
    return None


async def process_batch_via_mcp(batch_num: int, offset: int):
    """Process a batch of dishes using MCP tools."""
    global total_processed, total_success, total_failed
    
    # This function will be called with MCP tool results
    # For now, it's a placeholder that will be populated by actual MCP calls
    logger.info(f"Batch #{batch_num} processing will be handled via MCP tools")
    return {"processed": 0, "success": 0, "failed": 0}


# Main script - will use MCP tools to fetch and update
logger.info("✅ Enrichment script ready")
logger.info("💡 This script will be called via MCP tool interface")
logger.info("💡 Ollama is ready for enrichment requests")



