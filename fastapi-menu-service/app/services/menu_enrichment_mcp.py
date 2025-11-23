"""Menu enrichment service using MCP Supabase directly."""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from app.services.puter_qwen_service import OllamaQwenService
from datetime import datetime

logger = logging.getLogger(__name__)


class MenuEnrichmentMCPService:
    """Service for enriching menu dishes using MCP Supabase."""
    
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "qwen3:8b"):
        self.qwen_service = OllamaQwenService(base_url=ollama_url, model=model)
        # MCP Supabase will be called via tool interface
    
    async def enrich_batch_with_mcp(
        self,
        limit: int = 50,
        offset: int = 0,
        status_filter: str = "pending"
    ) -> Dict[str, Any]:
        """
        Enrich a batch using MCP Supabase.
        This method should be called from a context that has access to MCP tools.
        """
        # Fetch dishes - this will be done via MCP tool call
        # For now, return structure
        return {
            "processed": 0,
            "success": 0,
            "failed": 0,
            "message": "Use MCP tool calls directly"
        }

