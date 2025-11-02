# Dish Management & Health-Based Recommendations

## ✅ Features Implemented

### 1. Manual Dish Entry
- ✅ Create dishes with English names
- ✅ Add ingredients to dishes
- ✅ Store in Supabase database
- ✅ Admin API endpoints for management

### 2. Health-Based Recommendations
- ✅ Fever detection - marks dishes as "not recommended"
- ✅ Gastrointestinal symptoms - filters problematic dishes
- ✅ Visual indicators in frontend
- ✅ Reason explanations for recommendations

### 3. Dish Display in English
- ✅ All dishes shown in English
- ✅ Original names stored but English displayed
- ✅ Automatic matching with OCR results

## 🗄️ Database Setup

Run this SQL in Supabase SQL Editor:
```bash
fastapi-menu-service/supabase_dishes_schema.sql
```

This creates:
- `dishes` table - Store dish information
- `ingredients` table - Store ingredients
- `dish_ingredients` table - Link dishes to ingredients
- `health_dish_recommendations` table - Health-based filtering

## 📝 Adding Dishes

### Via API (Authenticated)

```bash
POST /api/v1/dishes/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name_original": "Poulet Grillé",
  "name_english": "Grilled Chicken",
  "description": "Tender grilled chicken with herbs",
  "category": "Main Course",
  "price_range": "$15-20",
  "ingredients": ["Chicken", "Garlic", "Herbs", "Oil"]
}
```

### Direct SQL

```sql
-- Add dish
INSERT INTO public.dishes (name_original, name_english, description, category)
VALUES ('Soupe à l''oignon', 'Onion Soup', 'French onion soup', 'Soup');

-- Add health recommendation
INSERT INTO public.health_dish_recommendations (condition_name, dish_id, recommendation_type, reason)
SELECT 'fever', id, 'not_recommended', 'Heavy/spicy foods can worsen fever'
FROM public.dishes
WHERE name_english = 'Onion Soup';
```

## 🔍 How Recommendations Work

### Fever Conditions
When user has **fever, flu, or cold**:
- ❌ Not Recommended: Heavy/spicy foods, complex dishes
- ✅ Recommended: Light soups, salads, easy-to-digest foods

### Gastrointestinal Symptoms
When user has **nausea, indigestion, stomach issues**:
- ❌ Not Recommended: Rich, fatty, spicy foods
- ✅ Recommended: Bland foods, clear soups, simple dishes

### Matching Logic
1. OCR extracts menu items (in any language)
2. System matches items to dishes in database (by English name)
3. Checks user's health conditions
4. Applies recommendations from database
5. Shows filtered results with reasons

## 🎯 Frontend Display

The frontend now shows:

1. **Health Advisory Banner** (if fever/GI detected)
   - Yellow warning box at top
   - Explains current health conditions

2. **Not Recommended Section**
   - Red borders and background
   - Shows dishes to avoid
   - Includes reason for each

3. **Recommended Section**
   - Green borders and background
   - Shows dishes that are good choices
   - Includes reason for each

4. **All Menu Items**
   - Full list with indicators
   - ⚠️ for not recommended
   - ✅ for recommended
   - Plain for neutral items

## 📊 Sample Data

The schema includes sample dishes:
- Grilled Chicken
- Caesar Salad
- Onion Soup
- Pasta Carbonara
- Seafood Stew
- Fruit Salad

With pre-configured recommendations for fever/GI symptoms.

## 🔧 API Endpoints

### Get All Dishes
```
GET /api/v1/dishes/
```

### Create Dish (Authenticated)
```
POST /api/v1/dishes/
Authorization: Bearer <token>
```

### Get Recommendations
```
GET /api/v1/dishes/recommendations?conditions=fever,gastrointestinal
```

### Filter Menu Items
```
GET /api/v1/dishes/filter?conditions=fever&menu_items=[...]
```

## 🧪 Testing

### Add a New Dish
```python
from app.services.dish_service import DishService

dish_service = DishService()
dish_id = await dish_service.create_dish(
    name_original="Bouillabaisse",
    name_english="Seafood Stew",
    description="Traditional fish stew",
    category="Soup",
    ingredients=["Fish", "Tomato", "Garlic", "Herbs"]
)
```

### Test Recommendations
```bash
# User with fever
curl "http://localhost:8000/api/v1/dishes/recommendations?conditions=fever"

# User with GI symptoms
curl "http://localhost:8000/api/v1/dishes/recommendations?conditions=gastrointestinal"
```

## 📝 Health Conditions Mapping

| Condition Name | Detected As |
|----------------|-------------|
| fever | Fever |
| flu | Fever |
| cold | Fever |
| gastrointestinal | GI |
| nausea | GI |
| indigestion | GI |
| stomach | GI |

## 🎨 UI Features

- ✅ Color-coded recommendations
- ✅ Clear visual indicators (⚠️ ✅)
- ✅ Reason explanations
- ✅ Health advisory banners
- ✅ All dishes in English
- ✅ Original names preserved in database

## 🚀 Usage Flow

1. **Admin adds dishes** to database with English names
2. **User uploads menu** image via OCR
3. **System detects** if user has fever/GI symptoms
4. **Matches menu items** to dishes in database
5. **Applies recommendations** based on health conditions
6. **Displays results** with clear recommendations

## ✅ Benefits

- **User Safety**: Prevents ordering foods that could worsen symptoms
- **Clear Guidance**: Explains why dishes are recommended/avoided
- **Multilingual Support**: Shows everything in English regardless of menu language
- **Database-Driven**: Easy to add/edit dishes and recommendations

