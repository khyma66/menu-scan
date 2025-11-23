#!/usr/bin/env python3
"""
Process a batch of dishes: fetch via MCP, enrich via Ollama, update via MCP.
This script processes one batch and can be called repeatedly.
"""

import asyncio
import aiohttp
import json
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen3:8b"
BATCH_SIZE = 10

async def enrich_dish(dish_name, ingredients=None):
    """Enrich a dish using Ollama."""
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
        'options': {'temperature': 0.3, 'num_predict': 2000}
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'{OLLAMA_URL}/api/chat',
                json=payload,
                timeout=aiohttp.ClientTimeout(total=90)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data.get('message', {}).get('content', '')
                    # Clean JSON
                    if '```json' in content:
                        content = content.split('```json')[1].split('```')[0].strip()
                    elif '```' in content:
                        content = content.split('```')[1].split('```')[0].strip()
                    return json.loads(content)
    except Exception as e:
        logger.error(f"Error enriching {dish_name}: {e}")
    return {}

def build_update_query(dish_name, enrichment):
    """Build SQL update query."""
    parts = []
    
    if enrichment.get('ingredients'):
        ing_str = ', '.join(enrichment['ingredients']).replace("'", "''")
        parts.append(f'"ingredients_complete" = \'{ing_str}\'')
    
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
        return f'UPDATE public.menu SET {", ".join(parts)} WHERE "Dish Name" = \'{dish_escaped}\''
    return None

async def process_batch(dishes):
    """Process a batch of dishes."""
    success = 0
    failed = 0
    
    for dish in dishes:
        dish_name = dish.get('Dish Name', '').strip()
        if not dish_name:
            continue
        
        ingredients = dish.get('ingredients')
        
        # Enrich
        enrichment = await enrich_dish(dish_name, ingredients)
        
        if not enrichment:
            failed += 1
            logger.warning(f"❌ Failed to enrich: {dish_name[:40]}")
            continue
        
        # Build update query (will be executed via MCP)
        update_query = build_update_query(dish_name, enrichment)
        if update_query:
            # Store query for MCP execution
            logger.info(f"✅ Enriched: {dish_name[:50]} - Query ready for MCP")
            success += 1
            # Return queries for MCP execution
            yield {'dish_name': dish_name, 'query': update_query, 'success': True}
        else:
            failed += 1
    
    return success, failed

# This will be called with dishes from MCP
logger.info("✅ Batch processor ready")
logger.info("💡 Will process dishes fetched via MCP Supabase")



