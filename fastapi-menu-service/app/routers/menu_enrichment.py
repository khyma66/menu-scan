"""Router for menu enrichment endpoints."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging
from app.services.menu_enrichment_service import MenuEnrichmentService
from app.config import settings
# Note: MCP Supabase tools are called via the tool interface, not directly imported

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/menu-enrichment", tags=["Menu Enrichment"])

# Initialize service with Ollama configuration
ollama_url = settings.ollama_url
ollama_model = settings.ollama_model
enrichment_service = MenuEnrichmentService(ollama_url=ollama_url, model=ollama_model)


def _escape_sql(value: Optional[str]) -> str:
    """Escape single quotes for SQL string literals."""
    return value.replace("'", "''") if value else ""


@router.get("/check-ollama")
async def check_ollama():
    """Check if Ollama is running and model is available."""
    try:
        is_available = await enrichment_service.qwen_service.check_ollama_available()
        return {
            "success": True,
            "ollama_available": is_available,
            "model": enrichment_service.qwen_service.model,
            "base_url": enrichment_service.qwen_service.base_url
        }
    except Exception as e:
        logger.error(f"Error checking Ollama: {e}")
        return {
            "success": False,
            "ollama_available": False,
            "error": str(e)
        }


@router.post("/enrich-batch")
async def enrich_batch(
    limit: int = Query(100, ge=1, le=500, description="Number of dishes to process"),
    offset: int = Query(0, ge=0, description="Starting offset"),
    status_filter: str = Query("pending", description="Filter by enrichment status")
):
    """
    Enrich a batch of menu dishes with ingredients and similarity data.
    
    Uses local Ollama Qwen3:8b model and MCP Supabase for database operations.
    """
    try:
        # Check Ollama availability first
        is_available = await enrichment_service.qwen_service.check_ollama_available()
        if not is_available:
            raise HTTPException(
                status_code=503,
                detail="Ollama is not available. Make sure Ollama is running (ollama serve) and model is pulled (ollama pull qwen3:8b)"
            )
        
        # Use MCP Supabase to fetch dishes via the service
        # The service will handle MCP calls internally
        # For now, use the enrichment service which handles this
        result = await enrichment_service.enrich_menu_batch(
            limit=limit,
            offset=offset,
            status_filter=status_filter
        )
        return {
            "success": True,
            "result": result
        }
        
        if not dishes:
            return {
                "success": True,
                "result": {"processed": 0, "success": 0, "failed": 0, "message": "No dishes found"}
            }
        
        # Prepare dishes for enrichment
        dish_list = []
        for dish in dishes:
            dish_name = dish.get("Dish Name") or dish.get("dish_name") or ""
            if dish_name:
                dish_list.append({
                    "dish_name": dish_name,
                    "description": dish.get("description") or dish.get("ingredients") or ""
                })
        
        if not dish_list:
            return {
                "success": True,
                "result": {"processed": 0, "success": 0, "failed": 0, "message": "No valid dishes found"}
            }
        
        # Enrich dishes with Ollama
        enrichment_results = await enrichment_service.qwen_service.batch_enrich_dishes(dish_list)
        
        # Update database with results using MCP Supabase
        success_count = 0
        failed_count = 0
        
        for i, enrichment in enumerate(enrichment_results):
            if i >= len(dish_list):
                break
                
            dish_name = dish_list[i]["dish_name"]
            
            try:
                # Build update query
                update_fields = []
                
                if enrichment.get("ingredients"):
                    ingredients_str = ", ".join(enrichment["ingredients"])
                    escaped_ingredients = _escape_sql(ingredients_str)
                    update_fields.append(f'"ingredients_complete" = \'{escaped_ingredients}\'')
                
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
                        similar = enrichment[key]
                        if len(similar) > 0 and similar[0].get("dish"):
                            dish_one = _escape_sql(similar[0]["dish"])
                            update_fields.append(f'"similar_{cuisine}_dish_1" = \'{dish_one}\'')
                            update_fields.append(f'"similar_{cuisine}_similarity_1" = {similar[0].get("similarity", 0)}')
                        if len(similar) > 1 and similar[1].get("dish"):
                            dish_two = _escape_sql(similar[1]["dish"])
                            update_fields.append(f'"similar_{cuisine}_dish_2" = \'{dish_two}\'')
                            update_fields.append(f'"similar_{cuisine}_similarity_2" = {similar[1].get("similarity", 0)}')
                
                update_fields.append('"enrichment_status" = \'completed\'')
                update_fields.append('"enrichment_updated_at" = NOW()')
                
                if update_fields:
                    escaped_name = _escape_sql(dish_name)
                    update_query = f'''
                        UPDATE public.menu
                        SET {', '.join(update_fields)}
                        WHERE "Dish Name" = '{escaped_name}'
                    '''
                    
                    mcp_supabase_execute_sql(query=update_query)
                    success_count += 1
                    logger.info(f"✅ Enriched: {dish_name}")
            
            except Exception as e:
                logger.error(f"❌ Failed to update {dish_name}: {e}")
                try:
                    escaped_name = _escape_sql(dish_name)
                    fail_query = f'''
                        UPDATE public.menu
                        SET enrichment_status = 'failed',
                            enrichment_updated_at = NOW()
                        WHERE "Dish Name" = '{escaped_name}'
                    '''
                    mcp_supabase_execute_sql(query=fail_query)
                except Exception:
                    pass
                failed_count += 1
        
        result = {
            "processed": len(enrichment_results),
            "success": success_count,
            "failed": failed_count
        }
        
        return {
            "success": True,
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enriching batch: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enrich-all")
async def enrich_all(
    batch_size: int = Query(100, ge=1, le=500, description="Batch size")
):
    """
    Enrich all pending dishes in batches.
    
    This will process all dishes with status 'pending' in batches.
    """
    try:
        result = await enrichment_service.enrich_all_pending(batch_size=batch_size)
        return {
            "success": True,
            "result": result,
            "message": f"Processed {result['total_processed']} dishes"
        }
    except Exception as e:
        logger.error(f"Error enriching all: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_enrichment_status():
    """Get enrichment status statistics."""
    try:
        result = enrichment_service.get_enrichment_status()
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        return result
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
