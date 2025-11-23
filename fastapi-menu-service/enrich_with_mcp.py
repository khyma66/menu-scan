#!/usr/bin/env python3
"""
Enrichment script using MCP Supabase directly for optimal performance.
"""

import asyncio
import sys
import logging
import time
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, '.')

from app.services.puter_qwen_service import OllamaQwenService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def enrich_with_mcp():
    """Enrich dishes using MCP Supabase and Ollama."""
    
    # Initialize Ollama service
    qwen_service = OllamaQwenService()
    
    # Check Ollama
    logger.info("Checking Ollama availability...")
    is_available = await qwen_service.check_ollama_available()
    if not is_available:
        logger.error("❌ Ollama is not available!")
        return
    
    logger.info("✅ Ollama is ready!")
    
    # Use MCP Supabase to fetch dishes
    logger.info("Fetching dishes from database...")
    
    # We'll use the MCP tool via a subprocess or direct API calls
    # For now, let's use curl to call MCP Supabase execute_sql
    
    batch_size = 50
    offset = 0
    total_success = 0
    total_failed = 0
    start_time = time.time()
    
    while True:
        # Fetch batch using MCP Supabase
        query = f'''
            SELECT 
                "Dish Name",
                ingredients,
                description
            FROM public.menu
            WHERE enrichment_status = 'pending'
            ORDER BY "Dish Name"
            LIMIT {batch_size}
            OFFSET {offset}
        '''
        
        # Use curl to call MCP (this is a workaround - in production use MCP client)
        import subprocess
        result = subprocess.run(
            ['curl', '-s', '-X', 'POST', 
             'http://localhost:8000/mcp/supabase/execute_sql',
             '-H', 'Content-Type: application/json',
             '-d', json.dumps({'query': query})],
            capture_output=True,
            text=True
        )
        
        # Alternative: Use direct Supabase REST API
        # For now, let's use the FastAPI endpoint that uses MCP internally
        import requests
        
        # Try using the enrichment endpoint which should handle MCP internally
        try:
            response = requests.post(
                f"http://localhost:8000/menu-enrichment/enrich-batch",
                params={
                    "limit": batch_size,
                    "offset": offset,
                    "status_filter": "pending"
                },
                timeout=300
            )
            
            if response.status_code == 200:
                data = response.json()
                result_data = data.get("result", {})
                processed = result_data.get("processed", 0)
                success = result_data.get("success", 0)
                failed = result_data.get("failed", 0)
                
                if processed == 0:
                    logger.info("✅ No more dishes to process!")
                    break
                
                total_success += success
                total_failed += failed
                
                elapsed = time.time() - start_time
                logger.info(f"✅ Batch {offset//batch_size + 1}: Processed {processed}, Success {success}, Failed {failed}")
                logger.info(f"📊 Total: Success {total_success}, Failed {total_failed}, Time: {elapsed/60:.1f}m")
                
                offset += batch_size
                await asyncio.sleep(1)
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                break
        except Exception as e:
            logger.error(f"Error: {e}")
            break
    
    total_time = time.time() - start_time
    logger.info(f"\n🎉 Complete! Success: {total_success}, Failed: {total_failed}, Time: {total_time/60:.1f}m")


if __name__ == "__main__":
    try:
        asyncio.run(enrich_with_mcp())
    except KeyboardInterrupt:
        logger.info("\n⚠️ Interrupted")
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())

