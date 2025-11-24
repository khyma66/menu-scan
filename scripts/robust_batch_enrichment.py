#!/usr/bin/env python3
"""
Robust batch enrichment with retries and error handling.
Processes dishes autonomously using MCP Supabase and Ollama.
"""

import asyncio
import aiohttp
import json
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

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
BATCH_SIZE = 10
BATCH_DELAY = 3
MIN_DELAY = 0.5
MAX_RETRIES = 3

last_request_time = 0
total_processed = 0
total_success = 0
total_failed = 0
start_time = time.time()


async def wait_for_rate_limit():
    """Rate limiting."""
    global last_request_time
    current_time = time.time()
    time_since_last = current_time - last_request_time
    if time_since_last < MIN_DELAY:
        await asyncio.sleep(MIN_DELAY - time_since_last)
    last_request_time = time.time()


async def enrich_dish_with_retry(dish_name: str, ingredients: Optional[str] = None, max_retries: int = MAX_RETRIES) -> Dict[str, Any]:
    """Enrich a dish with retry logic."""
    prompt = f'''Analyze dish "{dish_name}". Return JSON:
{{
    "ingredients": ["ingredient1", "ingredient2"],
    "vegetarian": true/false,
    "vegan": true/false,
    "non_vegetarian": true/false,
    "similar_mexican": [{{"dish": "name", "similarity": 85}}],
    "similar_european": [{{"dish": "name", "similarity": 82}}],
    "similar_south_american": [{{"dish": "name", "similarity": 80}}]
}}'''
    
    payload = {
        'model': OLLAMA_MODEL,
        'messages': [{'role': 'user', 'content': prompt}],
        'stream': False,
        'options': {'temperature': 0.3, 'num_predict': 1500}
    }
    
    for attempt in range(max_retries):
        await wait_for_rate_limit()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{OLLAMA_URL}/api/chat',
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data.get('message', {}).get('content', '')
                        
                        # Extract JSON
                        if '{' in content:
                            start = content.find('{')
                            end = content.rfind('}') + 1
                            if end > start:
                                try:
                                    parsed = json.loads(content[start:end])
                                    return parsed
                                except json.JSONDecodeError:
                                    # Try cleaning more
                                    cleaned = content[start:end].strip()
                                    if cleaned.startswith('{') and cleaned.endswith('}'):
                                        parsed = json.loads(cleaned)
                                        return parsed
                        
                        # If we got here, try to find JSON in markdown
                        if '```json' in content:
                            json_part = content.split('```json')[1].split('```')[0].strip()
                            return json.loads(json_part)
                        elif '```' in content:
                            parts = content.split('```')
                            for part in parts:
                                if part.strip().startswith('{'):
                                    return json.loads(part.strip())
                    
                    elif response.status != 200 and attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                        
        except asyncio.TimeoutError:
            if attempt < max_retries - 1:
                logger.warning(f"Timeout for {dish_name[:30]}, retrying ({attempt + 1}/{max_retries})...")
                await asyncio.sleep(2 ** attempt)
                continue
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Error for {dish_name[:30]}: {str(e)[:50]}, retrying...")
                await asyncio.sleep(2 ** attempt)
                continue
    
    return {}


def build_update_query(dish_name: str, enrichment: Dict[str, Any]) -> Optional[str]:
    """Build SQL update query."""
    if not enrichment:
        return None
    
    parts = []
    
    if enrichment.get('ingredients'):
        ing_str = ', '.join(enrichment['ingredients'])
        ing_escaped = ing_str.replace("'", "''")
        parts.append(f'"ingredients_complete" = \'{ing_escaped}\'')
    
    if 'vegetarian' in enrichment:
        parts.append(f'"vegetarian_flag" = {str(enrichment["vegetarian"]).lower()}')
    if 'vegan' in enrichment:
        parts.append(f'"vegan_flag" = {str(enrichment["vegan"]).lower()}')
    if 'non_vegetarian' in enrichment:
        parts.append(f'"non_vegetarian_flag" = {str(enrichment["non_vegetarian"]).lower()}')
    
    for cuisine in ['mexican', 'european', 'south_american']:
        key = f'similar_{cuisine}'
        if enrichment.get(key):
            for i, item in enumerate(enrichment[key][:2], 1):
                if item.get('dish'):
                    dish_escaped = item['dish'].replace("'", "''")
                    similarity = item.get('similarity', 0)
                    parts.append(f'"similar_{cuisine}_dish_{i}" = \'{dish_escaped}\'')
                    parts.append(f'"similar_{cuisine}_similarity_{i}" = {similarity}')
    
    if parts:
        parts.append('"enrichment_status" = \'completed\'')
        parts.append('"enrichment_updated_at" = NOW()')
        dish_escaped = dish_name.replace("'", "''")
        return f'UPDATE public.menu SET {", ".join(parts)} WHERE "Dish Name" = \'{dish_escaped}\' AND enrichment_status = \'pending\''
    
    return None


async def process_batch_autonomous(batch_num: int):
    """Process a batch autonomously using MCP tools."""
    global total_processed, total_success, total_failed
    
    # Fetch dishes via MCP (will be called externally)
    # For now, return structure for MCP integration
    logger.info(f"📦 Batch #{batch_num} ready for processing")
    return {
        "batch_num": batch_num,
        "ready": True
    }


# Main autonomous loop
async def autonomous_enrichment_loop():
    """Main autonomous enrichment loop."""
    global total_processed, total_success, total_failed
    
    logger.info("🚀 Starting Autonomous Enrichment Loop")
    logger.info("=" * 70)
    
    batch_num = 0
    offset = 0
    
    try:
        while True:
            batch_num += 1
            batch_start = time.time()
            
            logger.info(f"📦 Batch #{batch_num}: Fetching dishes (offset: {offset})...")
            
            # This will be handled via MCP tool calls
            # For demonstration, we'll process what we can
            
            await asyncio.sleep(BATCH_DELAY)
            
            # Check if we should continue (would check via MCP)
            if batch_num >= 1000:  # Safety limit
                logger.info("Reached batch limit, stopping")
                break
            
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
    finally:
        elapsed = time.time() - start_time
        logger.info("=" * 70)
        logger.info(f"📊 Session Summary:")
        logger.info(f"   Processed: {total_processed}")
        logger.info(f"   Success: {total_success}")
        logger.info(f"   Failed: {total_failed}")
        logger.info(f"   Time: {elapsed/3600:.2f} hours")


if __name__ == "__main__":
    logger.info("✅ Robust batch enrichment ready")
    logger.info("💡 This will be integrated with MCP Supabase tools")
    # asyncio.run(autonomous_enrichment_loop())



