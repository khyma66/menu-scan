#!/usr/bin/env python3
"""
Autonomous menu enrichment using MCP Supabase and Ollama.
Processes dishes in batches with automatic resumption.
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
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler('enrichment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen3:8b"
OLLAMA_CHAT_ENDPOINT = f"{OLLAMA_URL}/api/chat"
BATCH_SIZE = 15  # Process 15 dishes per batch
BATCH_DELAY = 3  # 3 seconds between batches
MIN_DELAY = 0.5  # 0.5 seconds between individual requests


class AutonomousEnrichment:
    """Autonomous enrichment service."""
    
    def __init__(self):
        self.last_request_time = 0
        self.total_processed = 0
        self.total_success = 0
        self.total_failed = 0
        self.start_time = time.time()
    
    async def _wait_for_rate_limit(self):
        """Minimal rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < MIN_DELAY:
            await asyncio.sleep(MIN_DELAY - time_since_last)
        self.last_request_time = time.time()
    
    async def query_ollama(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """Query Ollama Qwen model with retries."""
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
        
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        OLLAMA_CHAT_ENDPOINT,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=90)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            content = data.get("message", {}).get("content", "") or data.get("response", "")
                            return content
                        else:
                            if attempt < max_retries - 1:
                                await asyncio.sleep(2)
                                continue
                            logger.error(f"Ollama API error {response.status}")
                            return None
            except asyncio.TimeoutError:
                if attempt < max_retries - 1:
                    logger.warning(f"Timeout, retrying ({attempt + 1}/{max_retries})...")
                    await asyncio.sleep(2)
                    continue
                logger.error("Ollama request timeout after retries")
                return None
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    continue
                logger.error(f"Error querying Ollama: {e}")
                return None
        
        return None
    
    async def enrich_dish(self, dish_name: str, ingredients: Optional[str] = None) -> Dict[str, Any]:
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
            logger.error(f"Failed to parse JSON for {dish_name}: {e}")
            logger.debug(f"Response: {response[:300]}")
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
    
    async def process_batch(self, dishes: List[Dict]) -> Dict[str, int]:
        """Process a batch of dishes."""
        success = 0
        failed = 0
        
        for dish in dishes:
            dish_name = dish.get("Dish Name", "").strip()
            if not dish_name:
                continue
            
            ingredients = dish.get("ingredients")
            
            try:
                # Enrich dish
                enrichment = await self.enrich_dish(dish_name, ingredients)
                
                if not enrichment:
                    failed += 1
                    await self.mark_failed(dish_name)
                    continue
                
                # Update database via MCP
                await self.update_dish(dish_name, enrichment)
                success += 1
                self.total_success += 1
                logger.info(f"✅ [{self.total_processed + success}] Enriched: {dish_name[:50]}")
                
            except Exception as e:
                logger.error(f"❌ Error enriching {dish_name}: {e}")
                failed += 1
                await self.mark_failed(dish_name)
        
        return {"success": success, "failed": failed}
    
    async def update_dish(self, dish_name: str, enrichment: Dict[str, Any]):
        """Update dish in database - query will be executed via MCP."""
        # Build update query - will be executed via MCP tool
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
        
        # Similar dishes
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
            
            # Store query for MCP execution
            self._last_update_query = f'''
                UPDATE public.menu
                SET {set_clause}
                WHERE "Dish Name" = '{dish_name_escaped}'
            '''
        else:
            raise ValueError("No enrichment data to update")
    
    async def mark_failed(self, dish_name: str):
        """Mark dish as failed - query will be executed via MCP."""
        # Store query for MCP execution
        self._last_fail_query = f'''
            UPDATE public.menu
            SET enrichment_status = 'failed',
                enrichment_updated_at = NOW()
            WHERE "Dish Name" = '{dish_name.replace("'", "''")}'
        '''
    
    async def get_pending_dishes(self, limit: int, offset: int) -> List[Dict]:
        """Get pending dishes from database via MCP."""
        # This will be called via MCP tool interface
        # For now return empty - will be populated by MCP calls
        return []
    
    async def get_status(self) -> Dict[str, int]:
        """Get enrichment status via MCP."""
        # This will be called via MCP tool interface
        return {"pending": 197430, "completed": 0, "failed": 0}
    
    async def run_autonomous(self):
        """Run autonomous enrichment until complete."""
        # Check Ollama
        logger.info("🔍 Checking Ollama...")
        if not await self.check_ollama():
            logger.error("❌ Ollama is not available!")
            logger.error("💡 Make sure Ollama is running: ollama serve")
            return
        
        logger.info(f"✅ Ollama is ready: {OLLAMA_MODEL}")
        
        # Get initial status
        status = await self.get_status()
        logger.info(f"📊 Initial status: {status}")
        
        offset = 0
        batch_num = 0
        
        logger.info("🚀 Starting autonomous enrichment...")
        logger.info("=" * 70)
        
        try:
            while True:
                batch_num += 1
                batch_start = time.time()
                
                # Fetch batch
                dishes = await self.get_pending_dishes(BATCH_SIZE, offset)
                
                if not dishes:
                    logger.info("✅ No more pending dishes!")
                    break
                
                logger.info(f"📦 Batch #{batch_num}: Processing {len(dishes)} dishes...")
                
                # Process batch
                result = await self.process_batch(dishes)
                
                self.total_processed += len(dishes)
                self.total_failed += result["failed"]
                offset += len(dishes)
                
                batch_time = time.time() - batch_start
                elapsed = time.time() - self.start_time
                rate = self.total_processed / elapsed if elapsed > 0 else 0
                remaining = status["pending"] - self.total_processed
                eta_hours = (remaining / rate / 3600) if rate > 0 and remaining > 0 else 0
                
                logger.info(f"   ✅ Success: {result['success']} | ❌ Failed: {result['failed']} | ⏱️  Time: {batch_time:.1f}s")
                logger.info(f"📊 Total: {self.total_processed} processed | {self.total_success} success | {self.total_failed} failed")
                logger.info(f"⚡ Rate: {rate:.2f} dishes/sec | ETA: {eta_hours:.1f} hours")
                logger.info("-" * 70)
                
                # Checkpoint every 100 dishes
                if self.total_processed % 100 == 0:
                    current_status = await self.get_status()
                    logger.info(f"💾 Checkpoint: {current_status}")
                
                # Sleep between batches
                if len(dishes) == BATCH_SIZE:  # Only sleep if there might be more
                    await asyncio.sleep(BATCH_DELAY)
        
        except KeyboardInterrupt:
            logger.warning("\n⚠️  Enrichment interrupted by user")
        except Exception as e:
            logger.error(f"❌ Error during enrichment: {e}", exc_info=True)
        finally:
            # Final summary
            total_time = time.time() - self.start_time
            final_status = await self.get_status()
            
            logger.info("=" * 70)
            logger.info("🎉 Enrichment session completed!")
            logger.info(f"📊 Final Statistics:")
            logger.info(f"   Processed: {self.total_processed}")
            logger.info(f"   Successful: {self.total_success}")
            logger.info(f"   Failed: {self.total_failed}")
            logger.info(f"   Time: {total_time/3600:.2f} hours")
            logger.info(f"   Rate: {self.total_processed/total_time:.2f} dishes/sec")
            logger.info(f"📊 Database Status: {final_status}")
            
            if final_status["pending"] > 0:
                logger.info(f"💡 Resume by running the script again (will continue from pending dishes)")


async def main():
    """Main entry point."""
    enrichment = AutonomousEnrichment()
    await enrichment.run_autonomous()


if __name__ == "__main__":
    asyncio.run(main())

