-- Ingredients Database Schema for Menu OCR
-- Run this in your Supabase SQL editor

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For fuzzy text matching

-- Ingredients master table
CREATE TABLE IF NOT EXISTS public.ingredients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL, -- 'protein', 'vegetable', 'grain', 'dairy', 'spice', 'oil', 'sweetener', etc.
    common_names TEXT[], -- Alternative names and spellings
    nutritional_info JSONB, -- Calories, macros, vitamins, etc.
    allergens TEXT[], -- Common allergens this ingredient may contain
    health_benefits TEXT[], -- Health benefits
    health_concerns TEXT[], -- Health concerns or restrictions
    is_vegetarian BOOLEAN DEFAULT true,
    is_vegan BOOLEAN DEFAULT true,
    is_gluten_free BOOLEAN DEFAULT true,
    is_dairy_free BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Ingredient synonyms for better matching
CREATE TABLE IF NOT EXISTS public.ingredient_synonyms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ingredient_id UUID REFERENCES public.ingredients(id) ON DELETE CASCADE,
    synonym TEXT NOT NULL,
    language TEXT DEFAULT 'en',
    confidence_score DECIMAL(3,2) DEFAULT 1.0, -- How confident we are in this synonym
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(ingredient_id, synonym, language)
);

-- Menu items to ingredients mapping (many-to-many)
CREATE TABLE IF NOT EXISTS public.menu_item_ingredients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    menu_item_name TEXT NOT NULL,
    ingredient_id UUID REFERENCES public.ingredients(id) ON DELETE CASCADE,
    quantity TEXT, -- e.g., "2 cups", "1 tbsp", "to taste"
    is_optional BOOLEAN DEFAULT false,
    confidence_score DECIMAL(3,2) DEFAULT 1.0, -- How confident we are in this mapping
    source TEXT DEFAULT 'qwen_extraction', -- Source of the mapping
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_ingredients_name ON public.ingredients USING gin(name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_ingredients_category ON public.ingredients(category);
CREATE INDEX IF NOT EXISTS idx_ingredients_common_names ON public.ingredients USING gin(common_names);
CREATE INDEX IF NOT EXISTS idx_ingredients_allergens ON public.ingredients USING gin(allergens);

CREATE INDEX IF NOT EXISTS idx_synonyms_synonym ON public.ingredient_synonyms USING gin(synonym gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_synonyms_ingredient_id ON public.ingredient_synonyms(ingredient_id);

CREATE INDEX IF NOT EXISTS idx_menu_item_ingredients_name ON public.menu_item_ingredients USING gin(menu_item_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_menu_item_ingredients_ingredient_id ON public.menu_item_ingredients(ingredient_id);

-- Enable Row Level Security
ALTER TABLE public.ingredients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ingredient_synonyms ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.menu_item_ingredients ENABLE ROW LEVEL SECURITY;

-- RLS Policies (read access for all authenticated users)
CREATE POLICY "Authenticated users can read ingredients"
    ON public.ingredients FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users can read synonyms"
    ON public.ingredient_synonyms FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users can read menu item ingredients"
    ON public.menu_item_ingredients FOR SELECT
    USING (auth.role() = 'authenticated');

-- Insert comprehensive ingredient data
INSERT INTO public.ingredients (name, category, common_names, nutritional_info, allergens, health_benefits, health_concerns, is_vegetarian, is_vegan, is_gluten_free, is_dairy_free) VALUES
-- Proteins
('chicken breast', 'protein', ARRAY['chicken', 'chicken meat', 'boneless chicken'], '{"calories": 165, "protein": 31, "fat": 3.6}', ARRAY['none'], ARRAY['high_protein', 'lean_meat'], ARRAY['none'], true, false, true, true),
('salmon', 'protein', ARRAY['atlantic salmon', 'fresh salmon', 'salmon fillet'], '{"calories": 208, "protein": 22, "fat": 12, "omega3": "high"}', ARRAY['fish'], ARRAY['omega3', 'protein', 'healthy_fats'], ARRAY['mercury'], true, false, true, true),
('tofu', 'protein', ARRAY['firm tofu', 'silken tofu', 'soybean curd'], '{"calories": 76, "protein": 8, "fat": 4.8}', ARRAY['soy'], ARRAY['plant_protein', 'complete_protein'], ARRAY['soy_allergy'], true, true, true, true),
('eggs', 'protein', ARRAY['chicken eggs', 'whole eggs', 'fresh eggs'], '{"calories": 155, "protein": 13, "fat": 11}', ARRAY['eggs'], ARRAY['complete_protein', 'vitamins'], ARRAY['cholesterol'], true, false, true, true),

-- Vegetables
('spinach', 'vegetable', ARRAY['fresh spinach', 'baby spinach', 'leaf spinach'], '{"calories": 23, "fiber": 2.2, "iron": "high", "vitamin_k": "high"}', ARRAY['none'], ARRAY['iron', 'vitamins', 'antioxidants'], ARRAY['oxalate'], true, true, true, true),
('tomatoes', 'vegetable', ARRAY['fresh tomatoes', 'roma tomatoes', 'cherry tomatoes'], '{"calories": 18, "vitamin_c": "high", "lycopene": "high"}', ARRAY['none'], ARRAY['vitamin_c', 'antioxidants'], ARRAY['none'], true, true, true, true),
('onions', 'vegetable', ARRAY['yellow onions', 'red onions', 'white onions'], '{"calories": 40, "vitamin_c": 7.4}', ARRAY['none'], ARRAY['vitamin_c', 'antioxidants'], ARRAY['digestive_issues'], true, true, true, true),
('garlic', 'vegetable', ARRAY['fresh garlic', 'minced garlic', 'garlic cloves'], '{"calories": 149, "vitamin_c": 31.2}', ARRAY['none'], ARRAY['immune_boost', 'antioxidants'], ARRAY['digestive_issues'], true, true, true, true),

-- Grains
('rice', 'grain', ARRAY['white rice', 'brown rice', 'basmati rice'], '{"calories": 130, "carbs": 28, "fiber": 0.4}', ARRAY['none'], ARRAY['energy', 'fiber'], ARRAY['none'], true, true, true, true),
('quinoa', 'grain', ARRAY['white quinoa', 'red quinoa', 'black quinoa'], '{"calories": 222, "protein": 8.1, "fiber": 5.2}', ARRAY['none'], ARRAY['complete_protein', 'fiber'], ARRAY['none'], true, true, true, true),
('pasta', 'grain', ARRAY['spaghetti', 'penne', 'fettuccine'], '{"calories": 157, "carbs": 31}', ARRAY['wheat'], ARRAY['energy', 'fiber'], ARRAY['gluten'], true, true, false, true),

-- Dairy
('cheese', 'dairy', ARRAY['cheddar cheese', 'mozzarella', 'parmesan'], '{"calories": 402, "protein": 7, "fat": 33, "calcium": "high"}', ARRAY['dairy', 'milk'], ARRAY['calcium', 'protein'], ARRAY['lactose'], true, false, true, false),
('milk', 'dairy', ARRAY['whole milk', '2% milk', 'skim milk'], '{"calories": 61, "protein": 3.3, "calcium": "high"}', ARRAY['dairy', 'milk'], ARRAY['calcium', 'protein'], ARRAY['lactose'], true, false, true, false),
('butter', 'dairy', ARRAY['unsalted butter', 'salted butter'], '{"calories": 717, "fat": 81}', ARRAY['dairy', 'milk'], ARRAY['fat_soluble_vitamins'], ARRAY['saturated_fat'], true, false, true, false),

-- Spices & Herbs
('salt', 'spice', ARRAY['sea salt', 'table salt', 'kosher salt'], '{"sodium": "high"}', ARRAY['none'], ARRAY['electrolyte_balance'], ARRAY['sodium'], true, true, true, true),
('black pepper', 'spice', ARRAY['ground pepper', 'peppercorns'], '{"vitamin_k": 0.2}', ARRAY['none'], ARRAY['antioxidants'], ARRAY['none'], true, true, true, true),
('cumin', 'spice', ARRAY['ground cumin', 'cumin seeds'], '{"iron": 0.4}', ARRAY['none'], ARRAY['digestion', 'antioxidants'], ARRAY['none'], true, true, true, true),

-- Oils
('olive oil', 'oil', ARRAY['extra virgin olive oil', 'virgin olive oil'], '{"calories": 884, "healthy_fats": "high"}', ARRAY['none'], ARRAY['healthy_fats', 'antioxidants'], ARRAY['none'], true, true, true, true),
('vegetable oil', 'oil', ARRAY['canola oil', 'sunflower oil'], '{"calories": 884, "fat": 100}', ARRAY['none'], ARRAY['cooking_fat'], ARRAY['processed'], true, true, true, true),

-- Sweeteners
('sugar', 'sweetener', ARRAY['white sugar', 'granulated sugar', 'cane sugar'], '{"calories": 387, "carbs": 100}', ARRAY['none'], ARRAY['energy'], ARRAY['blood_sugar', 'empty_calories'], true, true, true, true),
('honey', 'sweetener', ARRAY['raw honey', 'pure honey'], '{"calories": 304, "antioxidants": "high"}', ARRAY['none'], ARRAY['antioxidants', 'energy'], ARRAY['blood_sugar'], true, true, true, true);

-- Insert common synonyms
INSERT INTO public.ingredient_synonyms (ingredient_id, synonym, confidence_score) VALUES
((SELECT id FROM ingredients WHERE name = 'chicken breast'), 'chicken', 0.9),
((SELECT id FROM ingredients WHERE name = 'chicken breast'), 'boneless chicken breast', 0.95),
((SELECT id FROM ingredients WHERE name = 'salmon'), 'fresh salmon', 0.9),
((SELECT id FROM ingredients WHERE name = 'tofu'), 'firm tofu', 0.9),
((SELECT id FROM ingredients WHERE name = 'eggs'), 'whole eggs', 0.95),
((SELECT id FROM ingredients WHERE name = 'spinach'), 'baby spinach', 0.9),
((SELECT id FROM ingredients WHERE name = 'tomatoes'), 'fresh tomatoes', 0.9),
((SELECT id FROM ingredients WHERE name = 'onions'), 'yellow onions', 0.8),
((SELECT id FROM ingredients WHERE name = 'garlic'), 'fresh garlic', 0.9),
((SELECT id FROM ingredients WHERE name = 'rice'), 'white rice', 0.9),
((SELECT id FROM ingredients WHERE name = 'quinoa'), 'white quinoa', 0.9),
((SELECT id FROM ingredients WHERE name = 'pasta'), 'spaghetti', 0.8),
((SELECT id FROM ingredients WHERE name = 'cheese'), 'cheddar cheese', 0.8),
((SELECT id FROM ingredients WHERE name = 'milk'), 'whole milk', 0.9),
((SELECT id FROM ingredients WHERE name = 'butter'), 'unsalted butter', 0.9),
((SELECT id FROM ingredients WHERE name = 'olive oil'), 'extra virgin olive oil', 0.95),
((SELECT id FROM ingredients WHERE name = 'sugar'), 'white sugar', 0.9),
((SELECT id FROM ingredients WHERE name = 'honey'), 'raw honey', 0.9);

-- Function to find ingredient matches with fuzzy search
CREATE OR REPLACE FUNCTION find_ingredient_matches(search_text TEXT, max_results INTEGER DEFAULT 10)
RETURNS TABLE (
    ingredient_id UUID,
    name TEXT,
    category TEXT,
    confidence_score DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        i.id,
        i.name,
        i.category,
        (similarity(i.name, search_text) * 1.0) as confidence_score
    FROM ingredients i
    WHERE i.name % search_text  -- pg_trgm similarity operator
       OR EXISTS (
           SELECT 1 FROM ingredient_synonyms s
           WHERE s.ingredient_id = i.id AND s.synonym % search_text
       )
    ORDER BY confidence_score DESC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Function to get ingredients for a menu item
CREATE OR REPLACE FUNCTION get_menu_item_ingredients(item_name TEXT)
RETURNS TABLE (
    ingredient_name TEXT,
    category TEXT,
    quantity TEXT,
    is_optional BOOLEAN,
    confidence_score DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        i.name,
        i.category,
        mi.quantity,
        mi.is_optional,
        mi.confidence_score
    FROM menu_item_ingredients mi
    JOIN ingredients i ON mi.ingredient_id = i.id
    WHERE mi.menu_item_name % item_name
    ORDER BY mi.confidence_score DESC;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT SELECT ON public.ingredients TO authenticated;
GRANT SELECT ON public.ingredient_synonyms TO authenticated;
GRANT SELECT ON public.menu_item_ingredients TO authenticated;

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add triggers
CREATE TRIGGER update_ingredients_updated_at BEFORE UPDATE ON public.ingredients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();