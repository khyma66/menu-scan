#!/usr/bin/env python3
"""
Start autonomous batch processing of menu enrichment.
Fetches batches, enriches via Ollama, updates via MCP Supabase.
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
        logging.FileHandler('batch_processing.log'),
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

stats = {
    "total_processed": 0,
    "total_success": 0,
    "total_failed": 0,
    "start_time": time.time(),
    "batch_num": 0
}


async def enrich_dish_ollama(dish_name: str) -> Dict[str, Any]:
    """Enrich dish using Ollama."""
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
        'prompt': prompt,
        'stream': False,
        'options': {'num_predict': 800, 'temperature': 0.3}
    }
    
    for attempt in range(MAX_RETRIES):
        await asyncio.sleep(MIN_DELAY)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{OLLAMA_URL}/api/generate',
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        resp = data.get('response', '')
                        
                        if '{' in resp:
                            start = resp.find('{')
                            end = resp.rfind('}') + 1
                            if end > start:
                                try:
                                    return json.loads(resp[start:end])
                                except json.JSONDecodeError:
                                    cleaned = resp[start:end].strip()
                                    if cleaned.startswith('{') and cleaned.endswith('}'):
                                        return json.loads(cleaned)
                    
                    elif attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                        
        except asyncio.TimeoutError:
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"Timeout for {dish_name[:30]}, retry {attempt + 1}/{MAX_RETRIES}")
                await asyncio.sleep(2 ** attempt)
                continue
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
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


async def process_batch_continuously():
    """Process batches continuously."""
    logger.info("🚀 Starting Continuous Batch Processing")
    logger.info("=" * 70)
    
    offset = 0
    
    try:
        while True:
            stats["batch_num"] += 1
            batch_start = time.time()
            
            logger.info(f"📦 Batch #{stats['batch_num']}: Fetching dishes (offset: {offset})...")
            
            # Fetch batch will be done via MCP tool calls
            # For now, we'll process what we can get
            
            # Process dishes (will be enriched and updated via MCP)
            await asyncio.sleep(BATCH_DELAY)
            
            offset += BATCH_SIZE
            
            # Log progress every 10 batches
            if stats["batch_num"] % 10 == 0:
                elapsed = time.time() - stats["start_time"]
                rate = stats["total_processed"] / elapsed if elapsed > 0 else 0
                logger.info(f"📊 Progress: {stats['total_processed']} processed | {stats['total_success']} success | {stats['total_failed']} failed | Rate: {rate:.2f}/sec")
            
            # Safety limit
            if stats["batch_num"] >= 10000:
                logger.info("Reached batch limit")
                break
            
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
    finally:
        elapsed = time.time() - stats["start_time"]
        logger.info("=" * 70)
        logger.info(f"📊 Final Statistics:")
        logger.info(f"   Batches: {stats['batch_num']}")
        logger.info(f"   Processed: {stats['total_processed']}")
        logger.info(f"   Success: {stats['total_success']}")
        logger.info(f"   Failed: {stats['total_failed']}")
        logger.info(f"   Time: {elapsed/3600:.2f} hours")


if __name__ == "__main__":
    logger.info("✅ Batch processor ready")
    logger.info("💡 Will process dishes fetched via MCP Supabase")
    # asyncio.run(process_batch_continuously())



