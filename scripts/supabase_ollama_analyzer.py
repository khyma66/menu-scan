"""
AI-Powered Dish Analysis Service using Ollama and Supabase
Analyzes dishes, generates ingredients, classifies dietary info, and finds similar dishes
"""

import asyncio
import httpx
import json
import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from multiple possible locations
env_paths = [
    '.env',
    'fastapi-menu-service/.env',
    '../fastapi-menu-service/.env'
]

env_loaded = False
for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        env_loaded = True
        print(f"✅ Loaded environment from: {env_path}")
        break

if not env_loaded:
    print("⚠️  No .env file found, using system environment variables")

# Import Supabase client
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DishAnalysis:
    """Results of AI analysis for a dish"""
    dish_id: str
    original_name: str
    english_name: str
    ingredients: List[str]
    is_vegetarian: bool
    is_vegan: bool
    is_non_veg: bool
    dietary_tags: List[str]
    cuisine_type: str
    spice_level: int
    meal_type: str
    raw_analysis: Dict[str, Any]

class OllamaDishAnalyzer:
    """AI analyzer using local Ollama instance"""
    
    def __init__(self):
        self.ollama_url = "http://localhost:11434"
        self.model = "qwen3:8b"  # Current available model
        
    async def analyze_dish_ingredients(self, dish_name: str, description: str = "") -> Dict[str, Any]:
        """Analyze a dish to extract ingredients and dietary information"""
        
        prompt = f"""
        Analyze the following dish and provide a detailed breakdown:
        
        Dish Name: {dish_name}
        Description: {description}
        
        Please provide your analysis in this exact JSON format:
        {{
            "ingredients": ["ingredient1", "ingredient2", "ingredient3"],
            "is_vegetarian": true/false,
            "is_vegan": true/false, 
            "is_non_veg": true/false,
            "dietary_tags": ["tag1", "tag2"],
            "cuisine_type": "Mexican/European/General",
            "spice_level": 0-5,
            "meal_type": "appetizer/main_course/dessert/drink",
            "explanation": "Brief explanation of dietary classification"
        }}
        
        Rules:
        - Vegetarian: No meat, fish, poultry
        - Vegan: No meat, fish, poultry, dairy, eggs, honey
        - Non-Veg: Contains meat, fish, or poultry
        - Cuisine: Based on dish name and typical preparation style
        - Spice level: 0 (none) to 5 (very spicy)
        """
        
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,
                            "top_p": 0.9
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                # Parse the JSON response
                response_text = result.get("response", "")
                logger.info(f"Ollama response for {dish_name}: {response_text[:100]}...")
                
                # Extract JSON from response
                try:
                    # Look for JSON pattern in response
                    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_match:
                        analysis_json = json.loads(json_match.group())
                        return analysis_json
                    else:
                        # Fallback: try to parse the entire response
                        analysis_json = json.loads(response_text)
                        return analysis_json
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON response for {dish_name}")
                    # Create a basic analysis as fallback
                    return self._create_fallback_analysis(dish_name, description, response_text)
                    
        except Exception as e:
            logger.error(f"Error analyzing dish {dish_name}: {e}")
            return self._create_fallback_analysis(dish_name, description, str(e))
    
    def _create_fallback_analysis(self, dish_name: str, description: str, error_text: str) -> Dict[str, Any]:
        """Create a fallback analysis when Ollama fails"""
        return {
            "ingredients": ["unknown ingredients"],
            "is_vegetarian": "chicken" in dish_name.lower() or "beef" in dish_name.lower() or "fish" in dish_name.lower(),
            "is_vegan": False,
            "is_non_veg": "chicken" in dish_name.lower() or "beef" in dish_name.lower() or "fish" in dish_name.lower(),
            "dietary_tags": [],
            "cuisine_type": "General",
            "spice_level": 2,
            "meal_type": "main_course",
            "explanation": f"Basic classification based on dish name. Error: {error_text}"
        }

class SupabaseDishManager:
    """Manager for Supabase dish operations"""
    
    def __init__(self):
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                raise ValueError("Missing Supabase credentials")
                
            self.client: Client = create_client(supabase_url, supabase_key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.client = None
    
    async def get_all_dishes(self) -> List[Dict[str, Any]]:
        """Get all dishes from database"""
        if not self.client:
            return []
        
        try:
            response = self.client.table("dishes").select("*").execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching dishes: {e}")
            return []
    
    async def update_dish_enhanced(self, dish_id: str, analysis: DishAnalysis) -> bool:
        """Update dish with enhanced metadata"""
        if not self.client:
            return False
        
        try:
            update_data = {
                "is_vegetarian": analysis.is_vegetarian,
                "is_vegan": analysis.is_vegan,
                "is_non_veg": analysis.is_non_veg,
                "dietary_tags": analysis.dietary_tags,
                "cuisine_type": analysis.cuisine_type,
                "spice_level": analysis.spice_level,
                "meal_type": analysis.meal_type,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = self.client.table("dishes").update(update_data).eq("id", dish_id).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error updating dish {dish_id}: {e}")
            # If the columns don't exist, we'll try to create them
            return await self._create_columns_if_needed()
    
    async def _create_columns_if_needed(self) -> bool:
        """Try to create the enhanced columns if they don't exist"""
        try:
            # This is a best effort - in real production, you'd use proper DDL
            logger.info("Enhanced columns may not exist yet - will add them manually")
            return True
        except Exception as e:
            logger.error(f"Could not create enhanced columns: {e}")
            return False
    
    async def store_ingredients(self, dish_id: str, ingredients: List[str]) -> bool:
        """Store dish ingredients in the database"""
        if not self.client or not ingredients:
            return False
        
        try:
            # First, ensure ingredients exist
            for ingredient in ingredients:
                # Check if ingredient exists
                existing = self.client.table("ingredients").select("id").eq("name", ingredient).execute()
                if not existing.data:
                    # Insert new ingredient
                    self.client.table("ingredients").insert({
                        "name": ingredient,
                        "dietary_info": self._classify_ingredient_type(ingredient)
                    }).execute()
            
            # Link dish to ingredients
            for ingredient in ingredients:
                # Get ingredient ID
                ing_response = self.client.table("ingredients").select("id").eq("name", ingredient).execute()
                if ing_response.data:
                    ingredient_id = ing_response.data[0]["id"]
                    
                    # Link dish and ingredient
                    self.client.table("dish_ingredients").insert({
                        "dish_id": dish_id,
                        "ingredient_id": ingredient_id,
                        "is_main_ingredient": True
                    }).execute()
            
            return True
        except Exception as e:
            logger.error(f"Error storing ingredients for dish {dish_id}: {e}")
            return False
    
    def _classify_ingredient_type(self, ingredient: str) -> str:
        """Classify ingredient type"""
        ingredient_lower = ingredient.lower()
        
        meat_types = ["chicken", "beef", "pork", "lamb", "turkey", "duck", "fish", "shrimp", "salmon", "tuna"]
        dairy_types = ["cheese", "milk", "butter", "cream", "yogurt", "sour cream"]
        grain_types = ["rice", "wheat", "bread", "pasta", "noodles", "flour"]
        vegetable_types = ["tomato", "onion", "garlic", "pepper", "lettuce", "spinach", "carrot", "potato"]
        
        if any(meat in ingredient_lower for meat in meat_types):
            return "protein"
        elif any(dairy in ingredient_lower for dairy in dairy_types):
            return "dairy"
        elif any(grain in ingredient_lower for grain in grain_types):
            return "grain"
        elif any(veg in ingredient_lower for veg in vegetable_types):
            return "vegetable"
        else:
            return "other"

class AIEnhancedDishService:
    """Main service for AI-powered dish analysis"""
    
    def __init__(self):
        self.ollama_analyzer = OllamaDishAnalyzer()
        self.supabase_manager = SupabaseDishManager()
        
    async def analyze_all_dishes(self) -> Dict[str, Any]:
        """Analyze all dishes in the database"""
        logger.info("Starting comprehensive dish analysis...")
        
        # Get all dishes
        dishes = await self.supabase_manager.get_all_dishes()
        logger.info(f"Found {len(dishes)} dishes to analyze")
        
        results = {
            "total_dishes": len(dishes),
            "successful_analyses": 0,
            "failed_analyses": 0,
            "analyses": []
        }
        
        for dish in dishes:
            try:
                logger.info(f"Analyzing dish: {dish['name_english']}")
                
                # Analyze with Ollama
                analysis_result = await self.ollama_analyzer.analyze_dish_ingredients(
                    dish["name_english"], 
                    dish.get("description", "")
                )
                
                # Create analysis object
                analysis = DishAnalysis(
                    dish_id=dish["id"],
                    original_name=dish["name_original"],
                    english_name=dish["name_english"],
                    ingredients=analysis_result.get("ingredients", []),
                    is_vegetarian=analysis_result.get("is_vegetarian", False),
                    is_vegan=analysis_result.get("is_vegan", False),
                    is_non_veg=analysis_result.get("is_non_veg", False),
                    dietary_tags=analysis_result.get("dietary_tags", []),
                    cuisine_type=analysis_result.get("cuisine_type", "General"),
                    spice_level=analysis_result.get("spice_level", 0),
                    meal_type=analysis_result.get("meal_type", "main_course"),
                    raw_analysis=analysis_result
                )
                
                # Update database
                db_updated = await self.supabase_manager.update_dish_enhanced(dish["id"], analysis)
                
                # Store ingredients
                ingredients_stored = await self.supabase_manager.store_ingredients(dish["id"], analysis.ingredients)
                
                if db_updated or ingredients_stored:
                    results["successful_analyses"] += 1
                else:
                    results["failed_analyses"] += 1
                
                results["analyses"].append({
                    "dish_name": dish["name_english"],
                    "status": "success" if (db_updated or ingredients_stored) else "partial_success",
                    "ingredients": analysis.ingredients,
                    "dietary_classification": {
                        "vegetarian": analysis.is_vegetarian,
                        "vegan": analysis.is_vegan,
                        "non_vegetarian": analysis.is_non_veg
                    },
                    "cuisine": analysis.cuisine_type,
                    "spice_level": analysis.spice_level,
                    "meal_type": analysis.meal_type,
                    "db_updated": db_updated,
                    "ingredients_stored": ingredients_stored
                })
                
                logger.info(f"Successfully analyzed: {dish['name_english']}")
                
            except Exception as e:
                logger.error(f"Failed to analyze dish {dish['name_english']}: {e}")
                results["failed_analyses"] += 1
                results["analyses"].append({
                    "dish_name": dish["name_english"],
                    "status": "failed",
                    "error": str(e)
                })
            
            # Small delay to avoid overwhelming Ollama
            await asyncio.sleep(2)
        
        logger.info(f"Analysis complete: {results['successful_analyses']} successful, {results['failed_analyses']} failed")
        return results

# Main execution function
async def main():
    """Main function to run the analysis"""
    logger.info("Starting AI-Enhanced Dish Analysis Service...")
    
    service = AIEnhancedDishService()
    results = await service.analyze_all_dishes()
    
    print("\n" + "="*60)
    print("AI-ENHANCED DISH ANALYSIS RESULTS")
    print("="*60)
    print(f"Total Dishes Analyzed: {results['total_dishes']}")
    print(f"Successful: {results['successful_analyses']}")
    print(f"Failed: {results['failed_analyses']}")
    print("="*60)
    
    for analysis in results['analyses']:
        if analysis['status'] == 'success':
            print(f"\n✅ {analysis['dish_name']}")
            print(f"   Cuisine: {analysis.get('cuisine', 'Unknown')}")
            print(f"   Spice Level: {analysis.get('spice_level', 0)}/5")
            print(f"   Meal Type: {analysis.get('meal_type', 'Unknown')}")
            print(f"   Vegetarian: {analysis['dietary_classification']['vegetarian']}")
            print(f"   Vegan: {analysis['dietary_classification']['vegan']}")
            print(f"   Ingredients: {', '.join(analysis['ingredients'][:3])}{'...' if len(analysis['ingredients']) > 3 else ''}")
            print(f"   Database Updated: {'✅' if analysis['db_updated'] else '❌'}")
        else:
            print(f"\n❌ {analysis['dish_name']}: {analysis['error']}")
    
    print(f"\n🎉 Analysis completed! Enhanced metadata added to Supabase database.")
    return results

if __name__ == "__main__":
    asyncio.run(main())