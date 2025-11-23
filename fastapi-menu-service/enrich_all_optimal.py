#!/usr/bin/env python3
"""
Optimal menu enrichment script using Ollama Qwen3:8b.
Processes dishes in batches with progress tracking and error handling.
"""

import asyncio
import sys
import logging
import time
from datetime import datetime
from app.services.menu_enrichment_service import MenuEnrichmentService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler('enrichment.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


async def enrich_all_optimal(
    batch_size: int = 50,
    max_concurrent: int = 1,
    checkpoint_interval: int = 100
):
    """
    Enrich all pending dishes with optimal settings.
    
    Args:
        batch_size: Number of dishes per batch
        max_concurrent: Maximum concurrent batches (1 for sequential)
        checkpoint_interval: Log progress every N dishes
    """
    service = MenuEnrichmentService()
    
    # Check Ollama availability
    logger.info("Checking Ollama availability...")
    is_available = await service.qwen_service.check_ollama_available()
    if not is_available:
        logger.error("❌ Ollama is not available!")
        logger.error("💡 Make sure Ollama is running: ollama serve")
        logger.error("💡 Pull the model: ollama pull qwen3:8b")
        return
    
    logger.info(f"✅ Ollama is ready: {service.qwen_service.model}")
    
    # Get initial status
    status = service.get_enrichment_status()
    logger.info(f"📊 Initial status: {status.get('statistics', [])}")
    
    total_processed = 0
    total_success = 0
    total_failed = 0
    offset = 0
    start_time = time.time()
    
    logger.info(f"🚀 Starting enrichment with batch_size={batch_size}")
    logger.info("=" * 60)
    
    try:
        while True:
            # Process batch
            batch_start = time.time()
            result = await service.enrich_menu_batch(
                limit=batch_size,
                offset=offset,
                status_filter="pending"
            )
            batch_time = time.time() - batch_start
            
            processed = result.get("processed", 0)
            success = result.get("success", 0)
            failed = result.get("failed", 0)
            
            if processed == 0:
                logger.info("✅ No more pending dishes to process!")
                break
            
            total_processed += processed
            total_success += success
            total_failed += failed
            offset += batch_size
            
            # Calculate progress
            elapsed = time.time() - start_time
            rate = total_processed / elapsed if elapsed > 0 else 0
            eta_seconds = (197430 - total_processed) / rate if rate > 0 else 0
            eta_hours = eta_seconds / 3600
            
            # Log progress
            logger.info(f"📦 Batch completed: {processed} processed ({success} success, {failed} failed) in {batch_time:.1f}s")
            logger.info(f"📊 Total: {total_processed} processed | {total_success} success | {total_failed} failed")
            logger.info(f"⚡ Rate: {rate:.1f} dishes/sec | ETA: {eta_hours:.1f} hours")
            logger.info("-" * 60)
            
            # Checkpoint
            if total_processed % checkpoint_interval == 0:
                logger.info(f"💾 Checkpoint: {total_processed} dishes processed")
                status = service.get_enrichment_status()
                logger.info(f"📊 Current status: {status.get('statistics', [])}")
            
            # Brief pause between batches
            await asyncio.sleep(1)
        
        # Final summary
        total_time = time.time() - start_time
        logger.info("=" * 60)
        logger.info("🎉 Enrichment completed!")
        logger.info(f"📊 Final Statistics:")
        logger.info(f"   Total processed: {total_processed}")
        logger.info(f"   Successful: {total_success}")
        logger.info(f"   Failed: {total_failed}")
        logger.info(f"   Total time: {total_time/3600:.2f} hours")
        logger.info(f"   Average rate: {total_processed/total_time:.2f} dishes/sec")
        
        # Final status
        status = service.get_enrichment_status()
        logger.info(f"📊 Final status: {status.get('statistics', [])}")
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Enrichment interrupted by user")
        logger.info(f"📊 Progress saved: {total_processed} dishes processed")
        logger.info(f"💡 Resume by running the script again (it will continue from pending dishes)")
    except Exception as e:
        logger.error(f"❌ Error during enrichment: {e}", exc_info=True)
        logger.info(f"📊 Progress saved: {total_processed} dishes processed")


if __name__ == "__main__":
    # Parse command line arguments
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    max_concurrent = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    
    logger.info(f"Starting optimal enrichment: batch_size={batch_size}, max_concurrent={max_concurrent}")
    
    asyncio.run(enrich_all_optimal(
        batch_size=batch_size,
        max_concurrent=max_concurrent,
        checkpoint_interval=100
    ))



