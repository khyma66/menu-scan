#!/usr/bin/env python3
"""
Start menu enrichment using Ollama Qwen3:8b.
Uses MCP Supabase for database operations.
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.puter_qwen_service import OllamaQwenService
from app.services.supabase_client import SupabaseClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def check_ollama():
    """Check if Ollama is available."""
    service = OllamaQwenService()
    return await service.check_ollama_available()


async def enrich_batch_via_mcp(batch_size=50, offset=0):
    """
    Enrich a batch of dishes using MCP Supabase and Ollama.
    This function uses MCP tools directly.
    """
    # Import MCP tools (these are available in the MCP context)
    # For now, we'll use a workaround
    
    qwen_service = OllamaQwenService()
    supabase = SupabaseClient()
    
    # Check Ollama
    if not await check_ollama():
        logger.error("Ollama not available!")
        return {"processed": 0, "success": 0, "failed": 0}
    
    logger.info(f"Starting enrichment batch: size={batch_size}, offset={offset}")
    
    # Note: Actual MCP calls need to be made via the API endpoint
    # This script is a helper to start the process
    logger.info("Use the API endpoint: POST /menu-enrichment/enrich-batch")
    logger.info("Or run: python3 enrich_optimal.py")
    
    return {"status": "ready", "message": "Use API endpoint or enrich_optimal.py"}


if __name__ == "__main__":
    logger.info("Menu Enrichment Starter")
    logger.info("=" * 60)
    
    # Check Ollama
    asyncio.run(check_ollama())
    
    logger.info("\nTo start enrichment, use:")
    logger.info("1. API: curl -X POST 'http://localhost:8000/menu-enrichment/enrich-batch?limit=50'")
    logger.info("2. Script: python3 enrich_optimal.py 50")
    logger.info("\nStarting optimal enrichment script...")
    
    # Import and run the optimal script
    import subprocess
    subprocess.run([sys.executable, "enrich_optimal.py", "50"])

