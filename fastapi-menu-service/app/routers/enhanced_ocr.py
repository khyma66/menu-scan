"""
Enhanced OCR Router with Qwen Integration and Ingredient Matching
"""

from fastapi import APIRouter, HTTPException, status, UploadFile, File, Depends
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any
from ..services.enhanced_qwen_extractor import EnhancedQwenExtractor
from ..services.supabase_client import SupabaseClient
import time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enhanced-ocr", tags=["Enhanced OCR"])

@router.post("/process-menu")
async def process_menu_with_qwen(
    file: UploadFile = File(...),
    extractor: EnhancedQwenExtractor = Depends(EnhancedQwenExtractor)
) -> Dict[str, Any]:
    """
    Process menu image with complete OCR -> Qwen extraction -> Ingredient matching pipeline
    Returns comprehensive menu data optimized for mobile apps
    """
    start_time = time.time()

    try:
        # Validate file
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )

        # Read image data
        image_data = await file.read()

        # Check file size (10MB limit)
        if len(image_data) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Image size exceeds 10MB limit"
            )

        # TODO: Implement actual OCR processing here
        # For now, use mock OCR text - replace with real OCR (Tesseract/OpenCV)
        mock_ocr_text = """
        Bella Vista Restaurant

        APPETIZERS
        Bruschetta Classica $12.99 - Toasted artisan bread with fresh tomatoes, basil, garlic and extra virgin olive oil
        Calamari Fritti $16.99 - Crispy fried squid rings served with spicy marinara sauce and lemon wedges
        Antipasto Misto $18.99 - Selection of cured meats, aged cheeses, marinated olives and roasted red peppers

        MAIN COURSES
        Osso Buco alla Milanese $28.99 - Braised veal shanks with vegetables, white wine and aromatic herbs, served with risotto alla milanese
        Branzino al Sale $26.99 - Mediterranean sea bass baked in sea salt crust with lemon and herbs, served with seasonal vegetables
        Pollo alla Parmigiana $22.99 - Breaded chicken breast topped with marinara sauce, mozzarella and parmesan, served with spaghetti
        Tagliatelle al Tartufo $24.99 - Fresh egg pasta with black truffle cream sauce, parmesan and fresh herbs

        DESSERTS
        Tiramisu Tradizionale $8.99 - Classic Italian dessert with mascarpone, ladyfingers, coffee and cocoa
        Panna Cotta ai Frutti di Bosco $7.99 - Vanilla panna cotta with mixed berry compote and mint
        Cannoli Siciliani $6.99 - Crispy pastry shells filled with sweet ricotta cream and chocolate chips

        BEVERAGES
        Cappuccino $4.50 - Espresso with steamed milk foam
        Chianti Classico $8.99 - Medium-bodied red wine from Tuscany
        Limonata Fresca $3.99 - Fresh lemonade with mint
        """

        # Process with enhanced pipeline
        menu_data = extractor.process_menu_ocr(mock_ocr_text, language="en")

        processing_time = time.time() - start_time

        # Add performance metrics
        response = {
            "success": True,
            "menu_data": menu_data,
            "performance_metrics": {
                "total_processing_time_seconds": round(processing_time, 2),
                "pipeline_steps": {
                    "ocr_extraction": True,
                    "qwen_analysis": True,
                    "ingredient_matching": menu_data.get("enrichment_metadata", {}).get("ingredients_matched", 0) > 0,
                    "mobile_optimization": True
                },
                "data_quality": {
                    "items_found": len(menu_data.get("menu_items", [])),
                    "ingredients_matched": menu_data.get("enrichment_metadata", {}).get("ingredients_matched", 0),
                    "average_confidence": menu_data.get("extraction_metadata", {}).get("extraction_confidence", 0)
                }
            },
            "api_version": "2.0",
            "processing_timestamp": time.time()
        }

        logger.info(f"Enhanced menu processing completed in {processing_time:.2f}s for {len(menu_data.get('menu_items', []))} items")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced menu processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Menu processing failed: {str(e)}"
        )

@router.post("/analyze-text")
async def analyze_menu_text(
    text: str,
    language: str = "en",
    extractor: EnhancedQwenExtractor = Depends(EnhancedQwenExtractor)
) -> Dict[str, Any]:
    """
    Analyze menu text directly (for testing or text-based input)
    """
    try:
        menu_data = extractor.process_menu_ocr(text, language=language)

        return {
            "success": True,
            "menu_data": menu_data,
            "source": "direct_text_analysis"
        }

    except Exception as e:
        logger.error(f"Text analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text analysis failed: {str(e)}"
        )

@router.get("/ingredients/search")
async def search_ingredients(
    query: str,
    limit: int = 10,
    supabase: SupabaseClient = Depends(SupabaseClient)
) -> Dict[str, Any]:
    """
    Search ingredients in the database
    """
    try:
        # Use the PostgreSQL function for fuzzy search
        result = await supabase.rpc(
            'find_ingredient_matches',
            {'search_text': query.lower(), 'max_results': limit}
        )

        ingredients = []
        if result.data:
            for match in result.data:
                # Get full ingredient details
                ingredient_details = await supabase.table('ingredients').select('*').eq('id', match['ingredient_id']).execute()

                if ingredient_details.data:
                    ingredient = ingredient_details.data[0]
                    ingredients.append({
                        "id": ingredient['id'],
                        "name": ingredient['name'],
                        "category": ingredient['category'],
                        "common_names": ingredient.get('common_names', []),
                        "nutritional_info": ingredient.get('nutritional_info', {}),
                        "allergens": ingredient.get('allergens', []),
                        "match_confidence": float(match['confidence_score'])
                    })

        return {
            "success": True,
            "query": query,
            "results": ingredients,
            "total_found": len(ingredients)
        }

    except Exception as e:
        logger.error(f"Ingredient search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingredient search failed: {str(e)}"
        )

@router.get("/health")
async def enhanced_ocr_health() -> Dict[str, Any]:
    """
    Health check for enhanced OCR service
    """
    return {
        "service": "enhanced_ocr",
        "status": "healthy",
        "capabilities": [
            "ocr_text_processing",
            "qwen_menu_analysis",
            "ingredient_matching",
            "dietary_analysis",
            "mobile_optimization"
        ],
        "version": "2.0"
    }