#!/usr/bin/env python3
"""
Script to enrich menu table with Qwen model via Puter.js.
Run this script to process dishes in batches with rate limiting.
"""

import asyncio
import sys
import logging
from app.services.menu_enrichment_service import MenuEnrichmentService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to enrich menu dishes."""
    service = MenuEnrichmentService()
    
    # Get command line arguments
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    
    logger.info(f"Starting menu enrichment with batch_size={batch_size}, limit={limit}")
    
    # Enrich dishes
    result = await service.enrich_menu_batch(limit=limit, offset=0, status_filter="pending")
    
    logger.info(f"Enrichment completed:")
    logger.info(f"  Processed: {result.get('processed', 0)}")
    logger.info(f"  Success: {result.get('success', 0)}")
    logger.info(f"  Failed: {result.get('failed', 0)}")
    
    if result.get('error'):
        logger.error(f"Error: {result['error']}")


if __name__ == "__main__":
    asyncio.run(main())



