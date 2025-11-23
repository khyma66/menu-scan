#!/usr/bin/env python3
"""
Autonomous batch processor using MCP Supabase and Ollama /api/generate.
Processes dishes continuously with retries and error handling.
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
BATCH_SIZE = 10
BATCH_DELAY = 3
MIN_DELAY = 0.5
MAX_RETRIES = 3

stats = {
    "total_processed": 0,
    "total_success": 0,
    "total_failed": 0,
    "start_time": time.time()
}


async def enrich_dish_generate(dish_name: str, max_retries: int = MAX_RETRIES) -> Dict[str, Any]:
    """Enrich dish using /api/generate endpoint."""
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
    
    for attempt in range(max_retries):
        await asyncio.sleep(MIN_DELAY)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{OLLAMA_URL}/api/generate',
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=25)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        resp = data.get('response', '')
                        
                        # Extract JSON
                        if '{' in resp:
                            start = resp.find('{')
                            end = resp.rfind('}') + 1
                            if end > start:
                                try:
                                    return json.loads(resp[start:end])
                                except json.JSONDecodeError:
                                    # Try cleaning
                                    cleaned = resp[start:end].strip()
                                    if cleaned.startswith('{') and cleaned.endswith('}'):
                                        return json.loads(cleaned)
                    
                    elif attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                        
        except asyncio.TimeoutError:
            if attempt < max_retries - 1:
                logger.warning(f"Timeout for {dish_name[:30]}, retry {attempt + 1}/{max_retries}")
                await asyncio.sleep(2 ** attempt)
                continue
        except Exception as e:
            if attempt < max_retries - 1:
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


async def process_batch_autonomous(dishes: List[Dict]) -> Dict[str, int]:
    """Process a batch of dishes."""
    success = 0
    failed = 0
    
    for dish_info in dishes:
        dish_name = dish_info.get('Dish Name', '').strip()
        if not dish_name:
            continue
        
        try:
            # Enrich
            enrichment = await enrich_dish_generate(dish_name)
            
            if not enrichment:
                failed += 1
                stats["total_failed"] += 1
                logger.warning(f"❌ Failed to enrich: {dish_name[:40]}")
                continue
            
            # Build update query
            update_query = build_update_query(dish_name, enrichment)
            
            if update_query:
                # Store query for MCP execution
                logger.info(f"✅ [{stats['total_processed'] + success + 1}] Enriched: {dish_name[:50]}")
                logger.debug(f"Update query ready for: {dish_name[:30]}")
                success += 1
                stats["total_success"] += 1
                # Query will be executed via MCP tool
                yield {'dish_name': dish_name, 'query': update_query, 'enrichment': enrichment}
            else:
                failed += 1
                stats["total_failed"] += 1
                
        except Exception as e:
            logger.error(f"❌ Error processing {dish_name[:40]}: {e}")
            failed += 1
            stats["total_failed"] += 1
    
    stats["total_processed"] += len(dishes)
    return {"success": success, "failed": failed}


logger.info("✅ Autonomous batch processor ready")
logger.info("💡 Will process dishes fetched via MCP Supabase")
logger.info("💡 Uses Ollama /api/generate endpoint")



