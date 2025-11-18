"""
Restaurant Discovery API with Google Places integration
"""

import os
import json
import googlemaps
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="Restaurant Discovery API", version="1.0.0")

# Google Maps configuration
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
if not GOOGLE_MAPS_API_KEY:
    logger.warning("GOOGLE_MAPS_API_KEY not set - using mock data")

# Initialize Google Maps client
try:
    gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY) if GOOGLE_MAPS_API_KEY else None
except Exception as e:
    logger.error(f"Failed to initialize Google Maps client: {e}")
    gmaps = None

# Restaurant category definitions
RESTAURANT_CATEGORIES = {
    'italian': {
        'name': 'Italian',
        'icon': '🍕',
        'google_types': ['italian_restaurant'],
        'yelp_categories': ['italian', 'pizza'],
        'keywords': ['pasta', 'pizza', 'risotto', 'gelato']
    },
    'mexican': {
        'name': 'Mexican',
        'icon': '🥘',
        'google_types': ['mexican_restaurant'],
        'yelp_categories': ['mexican', 'latin'],
        'keywords': ['taco', 'burrito', 'enchilada', 'quesadilla']
    },
    'chinese': {
        'name': 'Chinese',
        'icon': '🍜',
        'google_types': ['chinese_restaurant'],
        'yelp_categories': ['chinese', 'cantonese', 'szechuan'],
        'keywords': ['noodle', 'dumpling', 'fried rice', 'wok']
    },
    'indian': {
        'name': 'Indian',
        'icon': '🍛',
        'google_types': ['indian_restaurant'],
        'yelp_categories': ['indian', 'curry'],
        'keywords': ['curry', 'biryani', 'tikka', 'naan', 'masala']
    },
    'japanese': {
        'name': 'Japanese',
        'icon': '🍣',
        'google_types': ['japanese_restaurant'],
        'yelp_categories': ['japanese', 'sushi', 'ramen'],
        'keywords': ['sushi', 'ramen', 'tempura', 'udon', 'yakitori']
    },
    'american': {
        'name': 'American',
        'icon': '🍔',
        'google_types': ['american_restaurant'],
        'yelp_categories': ['american', 'burgers', 'bbq'],
        'keywords': ['burger', 'steak', 'bbq', 'comfort food']
    },
    'thai': {
        'name': 'Thai',
        'icon': '🍜',
        'google_types': ['thai_restaurant'],
        'yelp_categories': ['thai'],
        'keywords': ['pad thai', 'tom yum', 'green curry', 'satay']
    },
    'korean': {
        'name': 'Korean',
        'icon': '🍲',
        'google_types': ['korean_restaurant'],
        'yelp_categories': ['korean', 'bbq'],
        'keywords': ['bulgogi', 'kimchi', 'bibimbap', 'kimchi']
    }
}

# Mock data for development when Google API is not available
MOCK_RESTAURANTS = [
    {
        'place_id': 'mock_1',
        'name': 'Taj Mahal Indian Cuisine',
        'rating': 4.3,
        'price_level': 2,
        'vicinity': '123 Main St',
        'location': {'lat': 40.7128, 'lng': -74.0060},
        'types': ['indian_restaurant', 'establishment'],
        'opening_hours': {'open_now': True},
        'user_ratings_total': 234,
        'photos': [{'photo_reference': 'mock_photo_1'}]
    },
    {
        'place_id': 'mock_2',
        'name': 'Sakura Japanese Restaurant',
        'rating': 4.5,
        'price_level': 3,
        'vicinity': '456 Oak Ave',
        'location': {'lat': 40.7135, 'lng': -74.0065},
        'types': ['japanese_restaurant', 'establishment'],
        'opening_hours': {'open_now': True},
        'user_ratings_total': 156,
        'photos': [{'photo_reference': 'mock_photo_2'}]
    },
    {
        'place_id': 'mock_3',
        'name': 'Mama Mia Italian Bistro',
        'rating': 4.2,
        'price_level': 2,
        'vicinity': '789 Pine St',
        'location': {'lat': 40.7140, 'lng': -74.0055},
        'types': ['italian_restaurant', 'establishment'],
        'opening_hours': {'open_now': False},
        'user_ratings_total': 89,
        'photos': [{'photo_reference': 'mock_photo_3'}]
    }
]

class Restaurant(BaseModel):
    place_id: str
    name: str
    rating: Optional[float] = None
    price_level: Optional[int] = None
    vicinity: str
    lat: float
    lng: float
    distance: float = 0.0
    category: str
    open_now: Optional[bool] = None
    user_ratings_total: Optional[int] = None
    photo_url: Optional[str] = None

class NearbyRestaurantsResponse(BaseModel):
    restaurants: List[Restaurant]
    total_count: int
    location: Dict[str, float]
    category: str
    radius: int

class RestaurantSearchRequest(BaseModel):
    lat: float
    lng: float
    category: Optional[str] = None
    radius: int = 2000
    limit: int = 50
    offset: int = 0

def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two points in miles"""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 3959  # Earth radius in miles
    
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c

def detect_category(restaurant_data: Dict[str, Any]) -> str:
    """Detect primary category for a restaurant"""
    types = restaurant_data.get('types', [])
    name = restaurant_data.get('name', '').lower()
    
    # Google Places types
    for category, config in RESTAURANT_CATEGORIES.items():
        if any(restaurant_type in types for restaurant_type in config['google_types']):
            return category
            
    # Keyword matching
    for category, config in RESTAURANT_CATEGORIES.items():
        if any(keyword in name for keyword in config['keywords']):
            return category
            
    return 'american'  # default

def format_restaurant_data(place_data: Dict[str, Any], user_lat: float, user_lng: float) -> Restaurant:
    """Format Google Places data into Restaurant model"""
    location = place_data['geometry']['location']
    lat, lng = location['lat'], location['lng']
    
    # Calculate distance
    distance = calculate_distance(user_lat, user_lng, lat, lng)
    
    # Detect category
    category = detect_category(place_data)
    
    # Generate photo URL if available
    photo_url = None
    if 'photos' in place_data and place_data['photos']:
        photo_ref = place_data['photos'][0]['photo_reference']
        if GOOGLE_MAPS_API_KEY:
            photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_ref}&key={GOOGLE_MAPS_API_KEY}"
    
    return Restaurant(
        place_id=place_data['place_id'],
        name=place_data['name'],
        rating=place_data.get('rating'),
        price_level=place_data.get('price_level'),
        vicinity=place_data.get('vicinity', ''),
        lat=lat,
        lng=lng,
        distance=distance,
        category=category,
        open_now=place_data.get('opening_hours', {}).get('open_now'),
        user_ratings_total=place_data.get('user_ratings_total'),
        photo_url=photo_url
    )

async def search_nearby_restaurants(lat: float, lng: float, category: Optional[str] = None, radius: int = 2000) -> List[Dict[str, Any]]:
    """Search for nearby restaurants using Google Places API or mock data"""
    
    if gmaps and GOOGLE_MAPS_API_KEY:
        try:
            # Search for restaurants
            places_result = gmaps.places_nearby(
                location=(lat, lng),
                radius=radius,
                type='restaurant',
                open_now=False  # Get all restaurants, filter later
            )
            
            restaurants = places_result.get('results', [])
            
            # Apply category filtering if specified
            if category and category in RESTAURANT_CATEGORIES:
                category_types = RESTAURANT_CATEGORIES[category]['google_types']
                restaurants = [
                    r for r in restaurants 
                    if any(restaurant_type in r.get('types', []) for restaurant_type in category_types)
                ]
            
            return restaurants
            
        except Exception as e:
            logger.error(f"Google Places API error: {e}")
            # Fall back to mock data
            return MOCK_RESTAURANTS
    else:
        # Use mock data for development
        logger.info("Using mock restaurant data")
        
        # Filter mock data by category
        filtered_restaurants = MOCK_RESTAURANTS
        if category:
            filtered_restaurants = [
                r for r in MOCK_RESTAURANTS
                if detect_category(r) == category
            ]
        
        return filtered_restaurants

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Restaurant Discovery API",
        "version": "1.0.0",
        "categories": list(RESTAURANT_CATEGORIES.keys()),
        "docs": "/docs"
    }

@app.get("/api/categories", response_model=Dict[str, Dict[str, Any]])
async def get_categories():
    """Get available restaurant categories"""
    return RESTAURANT_CATEGORIES

@app.get("/api/restaurants/nearby", response_model=NearbyRestaurantsResponse)
async def get_nearby_restaurants(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    category: Optional[str] = Query(None, description="Restaurant category"),
    radius: int = Query(2000, description="Search radius in meters (max 50000)"),
    limit: int = Query(50, description="Maximum number of results"),
    offset: int = Query(0, description="Pagination offset")
):
    """
    Get restaurants near given location with optional category filtering
    """
    try:
        # Validate parameters
        if not (-90 <= lat <= 90):
            raise HTTPException(status_code=400, detail="Invalid latitude")
        if not (-180 <= lng <= 180):
            raise HTTPException(status_code=400, detail="Invalid longitude")
        if radius > 50000:  # Google Places API limit
            radius = 50000
        
        # Search for restaurants
        restaurants_data = await search_nearby_restaurants(lat, lng, category, radius)
        
        # Format restaurant data
        restaurants = []
        for place_data in restaurants_data[offset:offset+limit]:
            try:
                restaurant = format_restaurant_data(place_data, lat, lng)
                restaurants.append(restaurant)
            except Exception as e:
                logger.warning(f"Failed to format restaurant data: {e}")
                continue
        
        # Sort by distance
        restaurants.sort(key=lambda x: x.distance)
        
        return NearbyRestaurantsResponse(
            restaurants=restaurants,
            total_count=len(restaurants_data),
            location={"lat": lat, "lng": lng},
            category=category or "all",
            radius=radius
        )
        
    except Exception as e:
        logger.error(f"Error getting nearby restaurants: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/restaurants/{place_id}")
async def get_restaurant_details(place_id: str):
    """Get detailed information for a specific restaurant"""
    try:
        if gmaps and GOOGLE_MAPS_API_KEY:
            # Get detailed restaurant information
            place_details = gmaps.place(
                place_id=place_id,
                fields=['name', 'rating', 'price_level', 'formatted_address', 'formatted_phone_number', 
                       'website', 'opening_hours', 'photos', 'reviews', 'user_ratings_total']
            )
            
            if place_details['status'] != 'OK':
                raise HTTPException(status_code=404, detail="Restaurant not found")
            
            result = place_details['result']
            
            # Generate photo URLs
            photos = []
            if 'photos' in result:
                for photo in result['photos'][:5]:  # Limit to 5 photos
                    photo_ref = photo['photo_reference']
                    photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference={photo_ref}&key={GOOGLE_MAPS_API_KEY}"
                    photos.append(photo_url)
            
            return {
                "place_id": place_id,
                "name": result.get('name'),
                "rating": result.get('rating'),
                "price_level": result.get('price_level'),
                "address": result.get('formatted_address'),
                "phone": result.get('formatted_phone_number'),
                "website": result.get('website'),
                "opening_hours": result.get('opening_hours'),
                "photos": photos,
                "reviews_count": result.get('user_ratings_total', 0)
            }
        else:
            # Return mock data for development
            mock_restaurant = next((r for r in MOCK_RESTAURANTS if r['place_id'] == place_id), None)
            if not mock_restaurant:
                raise HTTPException(status_code=404, detail="Restaurant not found")
            
            return {
                "place_id": place_id,
                "name": mock_restaurant['name'],
                "rating": mock_restaurant['rating'],
                "price_level": mock_restaurant['price_level'],
                "address": mock_restaurant['vicinity'],
                "phone": "+1 (555) 123-4567",
                "website": "https://example.com",
                "opening_hours": {"open_now": True, "weekday_text": []},
                "photos": ["https://via.placeholder.com/400x300"],
                "reviews_count": mock_restaurant['user_ratings_total']
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting restaurant details: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/restaurants/search")
async def search_restaurants(request: RestaurantSearchRequest):
    """Post endpoint for restaurant search with body parameters"""
    return await get_nearby_restaurants(
        lat=request.lat,
        lng=request.lng,
        category=request.category,
        radius=request.radius,
        limit=request.limit,
        offset=request.offset
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "google_api_available": bool(gmaps and GOOGLE_MAPS_API_KEY),
        "mock_mode": not (gmaps and GOOGLE_MAPS_API_KEY)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)