# Menu Enrichment with Puter.js Qwen Model

## Overview
This system enriches the `menu` table with complete ingredients, dietary classifications (vegetarian/vegan/non-vegetarian), and similarity data for Mexican, European, and South American cuisines using the free Qwen model via Puter.js.

## Database Schema Changes

The following columns have been added to the `menu` table:

### Ingredients & Dietary
- `ingredients_complete` (TEXT) - Complete list of ingredients
- `vegetarian_flag` (BOOLEAN) - Vegetarian classification
- `vegan_flag` (BOOLEAN) - Vegan classification  
- `non_vegetarian_flag` (BOOLEAN) - Non-vegetarian classification

### Similar Dishes - Mexican Cuisine
- `similar_mexican_dish_1` (TEXT) - Top similar Mexican dish
- `similar_mexican_similarity_1` (INTEGER) - Similarity percentage (0-100)
- `similar_mexican_dish_2` (TEXT) - Second similar Mexican dish
- `similar_mexican_similarity_2` (INTEGER) - Similarity percentage (0-100)

### Similar Dishes - European Cuisine
- `similar_european_dish_1` (TEXT) - Top similar European dish
- `similar_european_similarity_1` (INTEGER) - Similarity percentage (0-100)
- `similar_european_dish_2` (TEXT) - Second similar European dish
- `similar_european_similarity_2` (INTEGER) - Similarity percentage (0-100)

### Similar Dishes - South American Cuisine
- `similar_south_american_dish_1` (TEXT) - Top similar South American dish
- `similar_south_american_similarity_1` (INTEGER) - Similarity percentage (0-100)
- `similar_south_american_dish_2` (TEXT) - Second similar South American dish
- `similar_south_american_similarity_2` (INTEGER) - Similarity percentage (0-100)

### Status Tracking
- `enrichment_status` (TEXT) - Status: 'pending', 'completed', 'failed'
- `enrichment_updated_at` (TIMESTAMP) - Last update timestamp

## Rate Limiting

The system implements conservative rate limiting to respect Puter.js limits:
- **6 seconds** minimum delay between requests
- **10 requests per minute** maximum
- **300 requests per hour** maximum
- **30 second pause** after every batch of 5 dishes

## API Endpoints

### 1. Enrich Batch
```
POST /menu-enrichment/enrich-batch?limit=100&offset=0&status_filter=pending
```
Processes a batch of dishes with the specified limit and offset.

### 2. Enrich All Pending
```
POST /menu-enrichment/enrich-all?batch_size=100
```
Processes all pending dishes in batches.

### 3. Get Status
```
GET /menu-enrichment/status
```
Returns statistics on enrichment status (pending/completed/failed counts).

## Usage

### Via API
```bash
# Check status
curl http://localhost:8000/menu-enrichment/status

# Enrich a batch of 10 dishes
curl -X POST "http://localhost:8000/menu-enrichment/enrich-batch?limit=10&offset=0"

# Enrich all pending (will take a very long time for 197k+ dishes!)
curl -X POST "http://localhost:8000/menu-enrichment/enrich-all?batch_size=10"
```

### Via Script
```bash
cd fastapi-menu-service
python enrich_menu_script.py 10 100
# Arguments: batch_size limit
```

## Current Status

- **Total dishes**: 197,430
- **Pending enrichment**: 197,430
- **Completed**: 0
- **Failed**: 0

## Processing Time Estimate

With rate limiting:
- ~6 seconds per dish
- ~10 dishes per minute
- ~600 dishes per hour
- **~329 hours** for all 197,430 dishes (13.7 days)

**Recommendation**: Process in smaller batches during off-peak hours or use multiple API keys if available.

## Notes

1. Puter.js is primarily a client-side library. The server-side API endpoint may need adjustment.
2. If Puter.js API doesn't work, consider alternatives:
   - Hugging Face Inference API (free tier available)
   - OpenAI API (paid)
   - Anthropic API (paid)
   - Local Qwen model deployment

3. The system automatically handles:
   - Rate limiting
   - Error retries (3 attempts)
   - Failed dish marking
   - Progress tracking

4. Similar dishes are based on:
   - Ingredient similarity
   - Cooking method
   - Flavor profile
   - Cultural context



