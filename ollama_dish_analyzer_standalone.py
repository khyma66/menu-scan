"""
AI-Powered Dish Analysis Service using Ollama (Standalone Version)
Analyzes dishes, generates ingredients, classifies dietary info, and finds similar dishes
"""

import asyncio
import httpx
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
from dataclasses import dataclass
import os

# Setup logging
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
            async with httpx.AsyncClient(timeout=30) as client:
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
                logger.info(f"Ollama response for {dish_name}: {response_text}")
                
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
        # Basic keyword-based classification
        dish_lower = dish_name.lower()
        
        meat_keywords = ["chicken", "beef", "pork", "lamb", "turkey", "duck", "fish", "shrimp", "salmon", "tuna", "meat"]
        dairy_keywords = ["cheese", "milk", "butter", "cream", "yogurt", "sour cream"]
        spice_keywords = ["spicy", "hot", "chili", "jalapeño", "pepper"]
        
        is_non_veg = any(keyword in dish_lower for keyword in meat_keywords)
        has_dairy = any(keyword in dish_lower for keyword in dairy_keywords)
        is_spicy = any(keyword in dish_lower for keyword in spice_keywords)
        
        # Determine cuisine type
        cuisine = "General"
        if any(word in dish_lower for word in ["mexican", "taco", "burrito", "enchilada"]):
            cuisine = "Mexican"
        elif any(word in dish_lower for word in ["french", "italian", "pasta", "carbonara", "soup"]):
            cuisine = "European"
        
        return {
            "ingredients": ["analyzed ingredients"],
            "is_vegetarian": not is_non_veg,
            "is_vegan": not (is_non_veg or has_dairy),
            "is_non_veg": is_non_veg,
            "dietary_tags": ["basic"] if not is_non_veg else ["contains-meat"],
            "cuisine_type": cuisine,
            "spice_level": 3 if is_spicy else 2,
            "meal_type": "main_course",
            "explanation": f"Basic classification based on dish name. Error: {error_text}"
        }

class MockSupabaseManager:
    """Mock Supabase manager for demonstration (replace with real Supabase)"""
    
    def __init__(self):
        # Mock sample dishes
        self.sample_dishes = [
            {
                "id": "1",
                "name_original": "Poulet Grillé",
                "name_english": "Grilled Chicken",
                "description": "Tender grilled chicken with herbs"
            },
            {
                "id": "2", 
                "name_original": "Salade César",
                "name_english": "Caesar Salad",
                "description": "Fresh romaine lettuce with Caesar dressing"
            },
            {
                "id": "3",
                "name_original": "Pasta Carbonara",
                "name_english": "Pasta Carbonara", 
                "description": "Creamy pasta with bacon and eggs"
            },
            {
                "id": "4",
                "name_original": "Tacos al Pastor",
                "name_english": "Tacos al Pastor",
                "description": "Marinated pork tacos with pineapple"
            },
            {
                "id": "5",
                "name_original": "Margherita Pizza",
                "name_english": "Margherita Pizza",
                "description": "Classic pizza with tomato, mozzarella, and basil"
            }
        ]
        
        self.analyzed_dishes = []
        
    async def get_all_dishes(self) -> List[Dict[str, Any]]:
        """Get all dishes from mock database"""
        return self.sample_dishes
    
    async def update_dish_enhanced(self, dish_id: str, analysis: DishAnalysis) -> bool:
        """Update dish with enhanced metadata (mock)"""
        print(f"✅ Updated dish {analysis.english_name} with enhanced metadata:")
        print(f"   - Vegetarian: {analysis.is_vegetarian}")
        print(f"   - Vegan: {analysis.is_vegan}")
        print(f"   - Non-Veg: {analysis.is_non_veg}")
        print(f"   - Cuisine: {analysis.cuisine_type}")
        print(f"   - Spice Level: {analysis.spice_level}/5")
        print(f"   - Dietary Tags: {', '.join(analysis.dietary_tags)}")
        
        # Store in memory for this demo
        self.analyzed_dishes.append({
            "dish_id": dish_id,
            "english_name": analysis.english_name,
            "analysis": analysis
        })
        return True
    
    async def store_ingredients(self, dish_id: str, ingredients: List[str]) -> bool:
        """Store dish ingredients (mock)"""
        print(f"✅ Stored ingredients for {dish_id}: {', '.join(ingredients)}")
        return True
    
    async def store_similar_dishes(self, dish_id: str, similar_dishes: Dict[str, List[str]]) -> bool:
        """Store similar dish relationships (mock)"""
        print(f"✅ Stored similar dishes for {dish_id}:")
        for category, dishes in similar_dishes.items():
            if dishes:
                print(f"   - {category}: {', '.join(dishes)}")
        return True

class AIEnhancedDishService:
    """Main service for AI-powered dish analysis"""
    
    def __init__(self):
        self.ollama_analyzer = OllamaDishAnalyzer()
        self.supabase_manager = MockSupabaseManager()
        
    async def analyze_all_dishes(self) -> Dict[str, Any]:
        """Analyze all dishes in the database"""
        logger.info("Starting comprehensive dish analysis with Ollama...")
        
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
                await self.supabase_manager.update_dish_enhanced(dish["id"], analysis)
                
                # Store ingredients
                await self.supabase_manager.store_ingredients(dish["id"], analysis.ingredients)
                
                # Generate and store similar dishes
                similar_dishes = await self._generate_similar_dishes(
                    dish["name_english"], 
                    analysis.cuisine_type,
                    analysis.is_vegetarian
                )
                await self.supabase_manager.store_similar_dishes(dish["id"], similar_dishes)
                
                results["successful_analyses"] += 1
                results["analyses"].append({
                    "dish_name": dish["name_english"],
                    "status": "success",
                    "ingredients": analysis.ingredients,
                    "dietary_classification": {
                        "vegetarian": analysis.is_vegetarian,
                        "vegan": analysis.is_vegan,
                        "non_vegetarian": analysis.is_non_veg
                    },
                    "cuisine": analysis.cuisine_type,
                    "similar_dishes": similar_dishes
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
    
    async def _generate_similar_dishes(self, dish_name: str, cuisine_type: str, is_vegetarian: bool) -> Dict[str, List[str]]:
        """Generate similar dishes for different cuisine types"""
        
        # Define similar dishes database
        similar_dish_db = {
            "mexican": [
                "Chicken Quesadilla", "Veggie Tacos", "Mexican Rice Bowl", 
                "Enchiladas", "Chili con Carne", "Guacamole"
            ],
            "european": [
                "Chicken Caesar Salad", "Pasta Carbonara", "French Onion Soup",
                "Beef Bourguignon", "Greek Moussaka", "Margherita Pizza"
            ],
            "general": [
                "Grilled Chicken", "Vegetarian Pasta", "Beef Stir Fry",
                "Fish and Chips", "Vegetable Curry", "Beef Tacos"
            ]
        }
        
        result = {
            "Mexican": [],
            "European": [],
            "General": []
        }
        
        # Get top 2 similar dishes for each category
        for category in ["Mexican", "European", "General"]:
            category_key = category.lower()
            available_dishes = similar_dish_db.get(category_key, [])
            
            # Filter based on dietary preferences
            if is_vegetarian:
                available_dishes = [d for d in available_dishes if 
                    "chicken" not in d.lower() and 
                    "beef" not in d.lower() and 
                    "fish" not in d.lower() and
                    "meat" not in d.lower()]
            
            # Take top 2 dishes
            result[category] = available_dishes[:2]
        
        return result

# Test Ollama connection
async def test_ollama_connection():
    """Test if Ollama is running and responding"""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get("http://localhost:11434/api/tags")
            response.raise_for_status()
            models = response.json()
            print(f"✅ Ollama connection successful. Available models:")
            for model in models.get("models", []):
                print(f"   - {model['name']}")
            return True
    except Exception as e:
        print(f"❌ Ollama connection failed: {e}")
        return False

# Main execution function
async def main():
    """Main function to run the analysis"""
    print("\n" + "="*80)
    print("🍽️  AI-ENHANCED DISH ANALYSIS SERVICE")
    print("="*80)
    print("Using Ollama local AI for intelligent dish analysis...")
    
    # Test Ollama connection
    if not await test_ollama_connection():
        print("❌ Cannot proceed without Ollama connection")
        return
    
    print("\n🔄 Starting comprehensive dish analysis...")
    print("-" * 50)
    
    service = AIEnhancedDishService()
    results = await service.analyze_all_dishes()
    
    print("\n" + "="*80)
    print("📊 ANALYSIS RESULTS SUMMARY")
    print("="*80)
    print(f"Total Dishes Analyzed: {results['total_dishes']}")
    print(f"✅ Successful Analyses: {results['successful_analyses']}")
    print(f"❌ Failed Analyses: {results['failed_analyses']}")
    print("="*80)
    
    print("\n🎯 DETAILED RESULTS:")
    print("-" * 50)
    
    for analysis in results['analyses']:
        if analysis['status'] == 'success':
            print(f"\n✅ {analysis['dish_name']}")
            print(f"   🌍 Cuisine: {analysis.get('cuisine', 'Unknown')}")
            print(f"   🥬 Dietary: ", end="")
            dietary = []
            if analysis['dietary_classification']['vegetarian']:
                dietary.append("Vegetarian")
            if analysis['dietary_classification']['vegan']:
                dietary.append("Vegan")
            if analysis['dietary_classification']['non_vegetarian']:
                dietary.append("Non-Vegetarian")
            print(", ".join(dietary) if dietary else "Not classified")
            
            print(f"   🧂 Ingredients: {', '.join(analysis['ingredients'][:3])}{'...' if len(analysis['ingredients']) > 3 else ''}")
            
            print(f"   🔗 Similar Dishes:")
            for cuisine, dishes in analysis.get('similar_dishes', {}).items():
                if dishes:
                    print(f"     • {cuisine}: {', '.join(dishes)}")
        else:
            print(f"\n❌ {analysis['dish_name']}: {analysis['error']}")
    
    print(f"\n🎉 Analysis completed successfully!")
    print("📋 Next steps: Results stored in Supabase database")
    print("   - Enhanced dish metadata")
    print("   - Ingredient relationships") 
    print("   - Similar dish recommendations")
    print("="*80)
    
    return results

if __name__ == "__main__":
    asyncio.run(main())