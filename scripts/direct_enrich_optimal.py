#!/usr/bin/env python3
"""
Direct menu enrichment using Ollama and MCP Supabase.
Bypasses FastAPI backend for optimal performance.
"""

import asyncio
import aiohttp
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Ollama configuration
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen3:8b"
OLLAMA_CHAT_ENDPOINT = f"{OLLAMA_URL}/api/chat"

# Batch configuration
BATCH_SIZE = 20
MIN_DELAY = 0.5


class DirectEnrichmentService:
    """Direct enrichment service using Ollama and MCP Supabase."""
    
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


async def enrich_batch_direct(limit: int = 20, offset: int = 0):
    """Enrich a batch of dishes directly using Supabase client."""
    import os
    from supabase import create_client
    
    service = DirectEnrichmentService()
    
    # Initialize Supabase client
    supabase_url = os.getenv("SUPABASE_URL", "https://jlfqzcaospvspmzbvbxd.supabase.co")
    supabase_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_key:
        logger.error("❌ SUPABASE_KEY not found in environment")
        return {"processed": 0, "success": 0, "failed": 0}
    
    supabase = create_client(supabase_url, supabase_key)
    
    # Fetch pending dishes
    response = supabase.table("menu").select(
        '"Dish Name", ingredients, description'
    ).eq("enrichment_status", "pending").order("Dish Name").limit(limit).offset(offset).execute()
    
    dishes = response.data if hasattr(response, 'data') and response.data else []
    
    if not dishes:
        return {"processed": 0, "success": 0, "failed": 0}
    
    logger.info(f"Processing {len(dishes)} dishes...")
    
    success_count = 0
    failed_count = 0
    
    for dish in dishes:
        dish_name = dish.get("Dish Name") or dish.get("dish_name") or ""
        if not dish_name:
            continue
        
        description = dish.get("description") or dish.get("ingredients") or ""
        
        try:
            # Enrich dish
            enrichment = await service.enrich_dish(dish_name, description)
            
            if not enrichment:
                failed_count += 1
                continue
            
            # Build update query
            update_fields = []
            
            if enrichment.get("ingredients"):
                ingredients_str = ", ".join(enrichment["ingredients"])
                update_fields.append(f'"ingredients_complete" = \'{ingredients_str.replace("'", "''")}\'')
            
            if "vegetarian" in enrichment:
                update_fields.append(f'"vegetarian_flag" = {str(enrichment["vegetarian"]).lower()}')
            if "vegan" in enrichment:
                update_fields.append(f'"vegan_flag" = {str(enrichment["vegan"]).lower()}')
            if "non_vegetarian" in enrichment:
                update_fields.append(f'"non_vegetarian_flag" = {str(enrichment["non_vegetarian"]).lower()}')
            
            # Similar dishes
            for cuisine in ["mexican", "european", "south_american"]:
                key = f"similar_{cuisine}"
                if enrichment.get(key):
                    dishes_list = enrichment[key]
                    for i, similar_dish in enumerate(dishes_list[:2], 1):
                        if similar_dish.get("dish"):
                            dish_name_escaped = similar_dish["dish"].replace("'", "''")
                            similarity = similar_dish.get("similarity", 0)
                            update_fields.append(f'"similar_{cuisine}_dish_{i}" = \'{dish_name_escaped}\'')
                            update_fields.append(f'"similar_{cuisine}_similarity_{i}" = {similarity}')
            
            if update_fields:
                # Build update dict for Supabase
                update_dict = {}
                
                # Parse fields and values
                update_values = []
                for field in update_fields:
                    if '=' in field:
                        parts = field.split('=', 1)
                        field_name = parts[0].strip().strip('"')
                        value = parts[1].strip().strip("'")
                        update_values.append((field_name, value))
                
                for field_name, value in update_values:
                    if value == "NOW()":
                        continue
                    elif value.lower() in ["true", "false"]:
                        update_dict[field_name] = value.lower() == "true"
                    elif value.isdigit():
                        update_dict[field_name] = int(value)
                    else:
                        update_dict[field_name] = value
                
                update_dict["enrichment_status"] = "completed"
                update_dict["enrichment_updated_at"] = datetime.now().isoformat()
                
                supabase.table("menu").update(update_dict).eq("Dish Name", dish_name).execute()
                success_count += 1
                logger.info(f"✅ Enriched: {dish_name}")
            else:
                failed_count += 1
                
        except Exception as e:
            logger.error(f"❌ Failed to enrich {dish_name}: {e}")
            # Mark as failed
            try:
                supabase.table("menu").update({
                    "enrichment_status": "failed",
                    "enrichment_updated_at": datetime.now().isoformat()
                }).eq("Dish Name", dish_name).execute()
            except:
                pass
            failed_count += 1
    
    return {
        "processed": len(dishes),
        "success": success_count,
        "failed": failed_count
    }


async def enrich_all_continuous():
    """Continuously enrich all pending dishes."""
    service = DirectEnrichmentService()
    
    # Check Ollama
    logger.info("Checking Ollama...")
    if not await service.check_ollama():
        logger.error("❌ Ollama is not available!")
        logger.error("💡 Make sure Ollama is running: ollama serve")
        logger.error(f"💡 Pull the model: ollama pull {OLLAMA_MODEL}")
        return
    
    logger.info(f"✅ Ollama is ready: {OLLAMA_MODEL}")
    
    total_processed = 0
    total_success = 0
    total_failed = 0
    offset = 0
    start_time = time.time()
    
    logger.info("🚀 Starting enrichment...")
    logger.info("=" * 60)
    
    try:
        while True:
            result = await enrich_batch_direct(limit=BATCH_SIZE, offset=offset)
            
            processed = result.get("processed", 0)
            success = result.get("success", 0)
            failed = result.get("failed", 0)
            
            if processed == 0:
                logger.info("✅ No more pending dishes!")
                break
            
            total_processed += processed
            total_success += success
            total_failed += failed
            offset += processed  # Use actual processed count
            
            elapsed = time.time() - start_time
            rate = total_processed / elapsed if elapsed > 0 else 0
            remaining = 197430 - total_processed
            eta_hours = (remaining / rate / 3600) if rate > 0 else 0
            
            logger.info(f"📦 Batch: {processed} ({success} success, {failed} failed) | Total: {total_processed} | Rate: {rate:.2f}/sec | ETA: {eta_hours:.1f}h")
            
            # Checkpoint every 100
            if total_processed % 100 == 0:
                logger.info(f"💾 Checkpoint: {total_processed} dishes processed")
            
            await asyncio.sleep(1)
        
        total_time = time.time() - start_time
        logger.info("=" * 60)
        logger.info(f"🎉 Completed! Processed: {total_processed} | Success: {total_success} | Failed: {total_failed}")
        logger.info(f"⏱️  Time: {total_time/3600:.2f} hours | Rate: {total_processed/total_time:.2f} dishes/sec")
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Interrupted. Progress saved.")
        logger.info(f"📊 Processed: {total_processed} dishes")


if __name__ == "__main__":
    asyncio.run(enrich_all_continuous())

