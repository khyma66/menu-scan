#!/usr/bin/env python3
"""
Optimal menu enrichment script using Ollama Qwen3:8b.
Processes dishes in optimal batches with progress tracking.
"""

import asyncio
import aiohttp
import sys
import logging
from datetime import datetime
from app.services.menu_enrichment_service import MenuEnrichmentService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def check_ollama_health():
    """Check if Ollama is running and model is available."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "http://localhost:11434/api/tags",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    if "qwen3:8b" in models:
                        logger.info("✅ Ollama is running and qwen3:8b is available")
                        return True
                    else:
                        logger.error(f"❌ Model qwen3:8b not found. Available: {models}")
                        logger.info("💡 Run: ollama pull qwen3:8b")
                        return False
                return False
    except Exception as e:
        logger.error(f"❌ Ollama is not available: {e}")
        logger.info("💡 Start Ollama: ollama serve")
        return False


async def enrich_continuously(batch_size=50, max_batches=None):
    """
    Continuously enrich dishes until all are processed.
    
    Args:
        batch_size: Number of dishes per batch (optimal: 50 for local Ollama)
        max_batches: Maximum number of batches to process (None = unlimited)
    """
    # Check Ollama first
    if not await check_ollama_health():
        logger.error("Cannot proceed without Ollama. Exiting.")
        sys.exit(1)
    
    service = MenuEnrichmentService()
    
    total_processed = 0
    total_success = 0
    total_failed = 0
    batch_count = 0
    offset = 0
    
    start_time = datetime.now()
    
    logger.info("=" * 60)
    logger.info("Starting optimal menu enrichment")
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Max batches: {max_batches or 'unlimited'}")
    logger.info("=" * 60)
    
    try:
        while True:
            if max_batches and batch_count >= max_batches:
                logger.info(f"Reached max batches limit ({max_batches})")
                break
            
            batch_count += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"Batch #{batch_count} - Processing {batch_size} dishes (offset: {offset})")
            logger.info(f"{'='*60}")
            
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
            
            # Calculate progress
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = total_processed / elapsed if elapsed > 0 else 0
            estimated_remaining = (197430 - total_processed) / rate if rate > 0 else 0
            
            logger.info(f"\n📊 Batch #{batch_count} Results:")
            logger.info(f"   Processed: {result['processed']}")
            logger.info(f"   ✅ Success: {result['success']}")
            logger.info(f"   ❌ Failed: {result['failed']}")
            logger.info(f"\n📈 Overall Progress:")
            logger.info(f"   Total Processed: {total_processed}")
            logger.info(f"   Total Success: {total_success}")
            logger.info(f"   Total Failed: {total_failed}")
            logger.info(f"   Rate: {rate:.2f} dishes/second")
            logger.info(f"   Estimated time remaining: {estimated_remaining/3600:.2f} hours")
            
            offset += batch_size
            
            # Brief pause between batches
            if result["processed"] > 0:
                logger.info("⏳ Brief pause before next batch...")
                await asyncio.sleep(2)
    
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Error: {e}", exc_info=True)
    finally:
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("\n" + "=" * 60)
        logger.info("Enrichment Summary")
        logger.info("=" * 60)
        logger.info(f"Total batches: {batch_count}")
        logger.info(f"Total processed: {total_processed}")
        logger.info(f"Total success: {total_success}")
        logger.info(f"Total failed: {total_failed}")
        logger.info(f"Time elapsed: {elapsed/3600:.2f} hours")
        logger.info(f"Average rate: {total_processed/elapsed:.2f} dishes/second" if elapsed > 0 else "N/A")


if __name__ == "__main__":
    # Optimal batch size for local Ollama: 50 dishes per batch
    # This balances throughput with memory usage
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    max_batches = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    asyncio.run(enrich_continuously(batch_size=batch_size, max_batches=max_batches))

