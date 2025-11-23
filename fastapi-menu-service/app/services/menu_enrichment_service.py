"""Service for enriching menu table with Qwen model via Ollama."""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from app.services.puter_qwen_service import OllamaQwenService
from app.services.supabase_client import SupabaseClient
import json
from datetime import datetime

logger = logging.getLogger(__name__)


def _escape_sql(value: Optional[str]) -> str:
    """Escape single quotes for SQL string literals."""
    return value.replace("'", "''") if value else ""


class MenuEnrichmentService:
    """Service for enriching menu dishes with ingredients and similarity data."""
    
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "qwen3:8b"):
        """
        Initialize menu enrichment service.
        
        Args:
            ollama_url: Ollama API URL (default: http://localhost:11434)
            model: Ollama model name (default: qwen3:8b)
        """
        self.qwen_service = OllamaQwenService(base_url=ollama_url, model=model)
        self.supabase = SupabaseClient()
    
    async def enrich_menu_batch(
        self,
        limit: int = 100,
        offset: int = 0,
        status_filter: str = "pending"
    ) -> Dict[str, Any]:
        """
        Enrich a batch of menu items.
        
        Args:
            limit: Number of dishes to process
            offset: Starting offset
            status_filter: Filter by enrichment_status ('pending', 'completed', 'failed')
        
        Returns:
            Summary of enrichment results
        """
        try:
            # Use MCP Supabase to execute SQL query directly
            # This works better than Supabase client for large queries
            dishes = []
            
            # Try Supabase client first if available
            if self.supabase.client:
                try:
                    response = self.supabase.client.table("menu").select(
                        '"Dish Name", ingredients, description, vegetarian, non_vegetarian'
                    ).eq("enrichment_status", status_filter).order("Dish Name").limit(limit).offset(offset).execute()
                    
                    dishes = response.data if hasattr(response, 'data') and response.data else []
                except Exception as e:
                    logger.warning(f"Supabase client query failed, using MCP: {e}")
            
            # Fallback: Return empty if no dishes found
            if not dishes:
                logger.info("No dishes found for enrichment")
                return {"processed": 0, "success": 0, "failed": 0}
            
            logger.info(f"Found {len(dishes)} dishes to enrich")
            
            # Prepare dishes for Qwen enrichment
            dish_list = []
            for dish in dishes:
                dish_name = dish.get("Dish Name") or dish.get("dish_name") or ""
                if dish_name:
                    dish_list.append({
                        "dish_name": dish_name,
                        "description": dish.get("description") or dish.get("ingredients") or ""
                    })
            
            if not dish_list:
                return {"processed": 0, "success": 0, "failed": 0}
            
            # Enrich dishes with Qwen
            enrichment_results = await self.qwen_service.batch_enrich_dishes(dish_list)
            
            # Update database with enrichment results
            success_count = 0
            failed_count = 0
            
            for i, enrichment in enumerate(enrichment_results):
                if i >= len(dish_list):
                    break
                    
                dish_name = dish_list[i]["dish_name"]
                
                try:
                    # Prepare update fields
                    update_fields = []
                    update_values = []
                    
                    # Ingredients
                    if enrichment.get("ingredients"):
                        ingredients_str = ", ".join(enrichment["ingredients"])
                        update_fields.append('"ingredients_complete"')
                        update_values.append(f"'{_escape_sql(ingredients_str)}'")
                    
                    # Dietary flags
                    if "vegetarian" in enrichment:
                        update_fields.append('"vegetarian_flag"')
                        update_values.append(str(enrichment["vegetarian"]).lower())
                    if "vegan" in enrichment:
                        update_fields.append('"vegan_flag"')
                        update_values.append(str(enrichment["vegan"]).lower())
                    if "non_vegetarian" in enrichment:
                        update_fields.append('"non_vegetarian_flag"')
                        update_values.append(str(enrichment["non_vegetarian"]).lower())
                    
                    # Similar Mexican dishes
                    if enrichment.get("similar_mexican"):
                        mexican = enrichment["similar_mexican"]
                        if len(mexican) > 0 and mexican[0].get("dish"):
                            update_fields.append('"similar_mexican_dish_1"')
                            update_values.append(f"'{_escape_sql(mexican[0]['dish'])}'")
                            update_fields.append('"similar_mexican_similarity_1"')
                            update_values.append(str(mexican[0].get("similarity", 0)))
                        if len(mexican) > 1 and mexican[1].get("dish"):
                            update_fields.append('"similar_mexican_dish_2"')
                            update_values.append(f"'{_escape_sql(mexican[1]['dish'])}'")
                            update_fields.append('"similar_mexican_similarity_2"')
                            update_values.append(str(mexican[1].get("similarity", 0)))
                    
                    # Similar European dishes
                    if enrichment.get("similar_european"):
                        european = enrichment["similar_european"]
                        if len(european) > 0 and european[0].get("dish"):
                            update_fields.append('"similar_european_dish_1"')
                            update_values.append(f"'{_escape_sql(european[0]['dish'])}'")
                            update_fields.append('"similar_european_similarity_1"')
                            update_values.append(str(european[0].get("similarity", 0)))
                        if len(european) > 1 and european[1].get("dish"):
                            update_fields.append('"similar_european_dish_2"')
                            update_values.append(f"'{_escape_sql(european[1]['dish'])}'")
                            update_fields.append('"similar_european_similarity_2"')
                            update_values.append(str(european[1].get("similarity", 0)))
                    
                    # Similar South American dishes
                    if enrichment.get("similar_south_american"):
                        sa = enrichment["similar_south_american"]
                        if len(sa) > 0 and sa[0].get("dish"):
                            update_fields.append('"similar_south_american_dish_1"')
                            update_values.append(f"'{_escape_sql(sa[0]['dish'])}'")
                            update_fields.append('"similar_south_american_similarity_1"')
                            update_values.append(str(sa[0].get("similarity", 0)))
                        if len(sa) > 1 and sa[1].get("dish"):
                            update_fields.append('"similar_south_american_dish_2"')
                            update_values.append(f"'{_escape_sql(sa[1]['dish'])}'")
                            update_fields.append('"similar_south_american_similarity_2"')
                            update_values.append(str(sa[1].get("similarity", 0)))
                    
                    # Add status and timestamp
                    update_fields.extend(['"enrichment_status"', '"enrichment_updated_at"'])
                    update_values.extend(["'completed'", "NOW()"])
                    
                    if update_fields:
                        # Build update dict for Supabase client
                        update_dict = {}
                        for field, value in zip(update_fields, update_values):
                            field_name = field.strip('"')
                            if value == "NOW()":
                                continue  # Skip, handled separately
                            elif value.lower() in ["true", "false"]:
                                update_dict[field_name] = value.lower() == "true"
                            elif value.isdigit():
                                update_dict[field_name] = int(value)
                            else:
                                update_dict[field_name] = value.strip("'")
                        
                        update_dict["enrichment_status"] = "completed"
                        update_dict["enrichment_updated_at"] = datetime.now().isoformat()
                        
                        self.supabase.client.table("menu").update(update_dict).eq("Dish Name", dish_name).execute()
                        
                        success_count += 1
                        logger.info(f"✅ Enriched: {dish_name}")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to update {dish_name}: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    # Mark as failed
                    try:
                        # Mark as failed using Supabase client
                        self.supabase.client.table("menu").update({
                            "enrichment_status": "failed",
                            "enrichment_updated_at": datetime.now().isoformat()
                        }).eq("Dish Name", dish_name).execute()
                    except Exception as fail_error:
                        logger.error(f"Failed to mark as failed: {fail_error}")
                    failed_count += 1
            
            return {
                "processed": len(enrichment_results),
                "success": success_count,
                "failed": failed_count
            }
        
        except Exception as e:
            logger.error(f"Error enriching menu batch: {e}")
            return {
                "processed": 0,
                "success": 0,
                "failed": 0,
                "error": str(e)
            }
