#!/usr/bin/env python3
"""
Optimal batch enrichment script for menu dishes.
Processes dishes in optimal batches with progress tracking.
"""

import asyncio
import sys
import logging
import time
from datetime import datetime
from app.services.menu_enrichment_service import MenuEnrichmentService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def enrich_all_optimal():
    """Enrich all pending dishes with optimal batch processing."""
    service = MenuEnrichmentService()
    
    # Check Ollama availability
    logger.info("Checking Ollama availability...")
    is_available = await service.qwen_service.check_ollama_available()
    if not is_available:
        logger.error("❌ Ollama is not available!")
        logger.error("💡 Make sure Ollama is running: ollama serve")
        logger.error("💡 Pull the model: ollama pull qwen3:8b")
        return
    
    logger.info("✅ Ollama is available and ready!")
    
    # Optimal batch size for local Ollama (can handle more than Puter.js)
    batch_size = 50  # Process 50 dishes per batch
    total_processed = 0
    total_success = 0
    total_failed = 0
    offset = 0
    start_time = time.time()
    
    logger.info(f"🚀 Starting enrichment with batch size: {batch_size}")
    logger.info("=" * 60)
    
    while True:
        batch_start = time.time()
        
        logger.info(f"\n📦 Processing batch starting at offset {offset}...")
        result = await service.enrich_menu_batch(
            limit=batch_size,
            offset=offset,
            status_filter="pending"
        )
        
        if result["processed"] == 0:
            logger.info("✅ No more pending dishes to process!")
            break
        
        total_processed += result["processed"]
        total_success += result["success"]
        total_failed += result["failed"]
        
        batch_time = time.time() - batch_start
        elapsed_time = time.time() - start_time
        
        # Calculate progress
        success_rate = (total_success / total_processed * 100) if total_processed > 0 else 0
        avg_time_per_dish = elapsed_time / total_processed if total_processed > 0 else 0
        estimated_remaining = 197430 - total_processed  # Approximate total
        estimated_time_remaining = estimated_remaining * avg_time_per_dish if avg_time_per_dish > 0 else 0
        
        logger.info(f"✅ Batch completed in {batch_time:.1f}s")
        logger.info(f"   Processed: {result['processed']} | Success: {result['success']} | Failed: {result['failed']}")
        logger.info(f"📊 Overall Progress:")
        logger.info(f"   Total Processed: {total_processed}")
        logger.info(f"   Total Success: {total_success} ({success_rate:.1f}%)")
        logger.info(f"   Total Failed: {total_failed}")
        logger.info(f"   Elapsed Time: {elapsed_time/60:.1f} minutes")
        logger.info(f"   Avg Time/Dish: {avg_time_per_dish:.2f}s")
        if estimated_time_remaining > 0:
            logger.info(f"   Est. Time Remaining: {estimated_time_remaining/3600:.1f} hours")
        logger.info("=" * 60)
        
        offset += batch_size
        
        # Brief pause between batches
        await asyncio.sleep(1)
    
    total_time = time.time() - start_time
    logger.info("\n" + "=" * 60)
    logger.info("🎉 ENRICHMENT COMPLETE!")
    logger.info("=" * 60)
    logger.info(f"Total Processed: {total_processed}")
    logger.info(f"Total Success: {total_success} ({total_success/total_processed*100:.1f}%)")
    logger.info(f"Total Failed: {total_failed}")
    logger.info(f"Total Time: {total_time/60:.1f} minutes ({total_time/3600:.1f} hours)")
    logger.info(f"Average Time per Dish: {total_time/total_processed:.2f}s")


if __name__ == "__main__":
    try:
        asyncio.run(enrich_all_optimal())
    except KeyboardInterrupt:
        logger.info("\n⚠️ Enrichment interrupted by user")
        logger.info("Progress has been saved. You can resume later.")
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        logger.error(traceback.format_exc())

