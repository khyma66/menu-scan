#!/usr/bin/env python3
"""
Batch processing with thermal monitoring and automatic breaks.
Processes batches, monitors system temperature, and pauses when needed.
"""

import asyncio
import aiohttp
import json
import logging
import time
import subprocess
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
THERMAL_THRESHOLD = 50  # Thermal level threshold for pausing
COOLDOWN_TIME = 30  # Seconds to wait when thermal threshold exceeded

stats = {
    "total_processed": 0,
    "total_success": 0,
    "total_failed": 0,
    "start_time": time.time(),
    "batch_num": 0,
    "thermal_pauses": 0
}


def check_temperature() -> int:
    """Check CPU thermal level (macOS)."""
    try:
        result = subprocess.run(
            ['sysctl', '-n', 'machdep.xcpm.cpu_thermal_level'],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            return int(result.stdout.strip())
    except:
        pass
    return 0


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


async def process_batch_with_thermal_check(dishes: List[Dict]) -> Dict[str, int]:
    """Process batch with thermal monitoring."""
    # Check temperature before processing
    thermal_level = check_temperature()
    
    if thermal_level > THERMAL_THRESHOLD:
        logger.warning(f"⚠️ Thermal level {thermal_level} exceeds threshold {THERMAL_THRESHOLD}")
        logger.info(f"💤 Pausing for {COOLDOWN_TIME} seconds to cool down...")
        stats["thermal_pauses"] += 1
        await asyncio.sleep(COOLDOWN_TIME)
        thermal_level = check_temperature()
        logger.info(f"🌡️ Thermal level after cooldown: {thermal_level}")
    
    success = 0
    failed = 0
    
    for dish_info in dishes:
        dish_name = dish_info.get('Dish Name', '').strip()
        if not dish_name:
            continue
        
        # Check temperature periodically
        if stats["total_processed"] % 5 == 0:
            thermal_level = check_temperature()
            if thermal_level > THERMAL_THRESHOLD:
                logger.warning(f"⚠️ Thermal level {thermal_level}, pausing...")
                await asyncio.sleep(COOLDOWN_TIME)
        
        try:
            enrichment = await enrich_dish_ollama(dish_name)
            
            if not enrichment:
                failed += 1
                stats["total_failed"] += 1
                continue
            
            update_query = build_update_query(dish_name, enrichment)
            if update_query:
                logger.info(f"✅ [{stats['total_processed'] + success + 1}] Enriched: {dish_name[:50]}")
                success += 1
                stats["total_success"] += 1
                # Query will be executed via MCP
            else:
                failed += 1
                stats["total_failed"] += 1
                
        except Exception as e:
            logger.error(f"❌ Error processing {dish_name[:40]}: {e}")
            failed += 1
            stats["total_failed"] += 1
    
    stats["total_processed"] += len(dishes)
    return {"success": success, "failed": failed}


logger.info("✅ Batch processor with thermal monitoring ready")
logger.info(f"🌡️ Thermal threshold: {THERMAL_THRESHOLD}")
logger.info(f"💤 Cooldown time: {COOLDOWN_TIME} seconds")



