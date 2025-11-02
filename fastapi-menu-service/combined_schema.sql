-- Supabase Database Schema for Menu OCR
-- Run this in your Supabase SQL editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    phone TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Health conditions table
CREATE TABLE IF NOT EXISTS public.health_conditions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
    condition_type TEXT NOT NULL CHECK (condition_type IN ('allergy', 'illness', 'dietary')),
    condition_name TEXT NOT NULL,
    severity TEXT CHECK (severity IN ('mild', 'moderate', 'severe')),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Menu suggestions table (for health-based filtering)
CREATE TABLE IF NOT EXISTS public.menu_suggestions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    condition_type TEXT NOT NULL,
    condition_name TEXT NOT NULL,
    restriction_type TEXT NOT NULL CHECK (restriction_type IN ('avoid', 'recommend', 'caution')),
    item_keywords TEXT[], -- Keywords to match menu items
    suggestion TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- OCR results table
CREATE TABLE IF NOT EXISTS public.ocr_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    result JSONB,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_health_conditions_user_id ON public.health_conditions(user_id);
CREATE INDEX IF NOT EXISTS idx_health_conditions_type ON public.health_conditions(condition_type);
CREATE INDEX IF NOT EXISTS idx_ocr_results_user_id ON public.ocr_results(user_id);
CREATE INDEX IF NOT EXISTS idx_menu_suggestions_condition ON public.menu_suggestions(condition_name);

-- Enable Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.health_conditions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ocr_results ENABLE ROW LEVEL SECURITY;

-- RLS Policies for users
CREATE POLICY "Users can view own profile" 
    ON public.users FOR SELECT 
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" 
    ON public.users FOR UPDATE 
    USING (auth.uid() = id);

-- RLS Policies for health_conditions
CREATE POLICY "Users can view own health conditions" 
    ON public.health_conditions FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own health conditions" 
    ON public.health_conditions FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own health conditions" 
    ON public.health_conditions FOR UPDATE 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own health conditions" 
    ON public.health_conditions FOR DELETE 
    USING (auth.uid() = user_id);

-- RLS Policies for ocr_results
CREATE POLICY "Users can view own OCR results" 
    ON public.ocr_results FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own OCR results" 
    ON public.ocr_results FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

-- Insert default menu suggestions based on common conditions
INSERT INTO public.menu_suggestions (condition_type, condition_name, restriction_type, item_keywords, suggestion) VALUES
-- Dietary restrictions
('dietary', 'vegetarian', 'avoid', ARRAY['meat', 'chicken', 'beef', 'pork', 'fish', 'seafood'], 'Avoid all meat products'),
('dietary', 'vegan', 'avoid', ARRAY['meat', 'chicken', 'beef', 'pork', 'fish', 'seafood', 'egg', 'dairy', 'butter', 'cheese'], 'Avoid all animal products'),
('dietary', 'gluten-free', 'avoid', ARRAY['wheat', 'bread', 'pasta', 'pizza', 'burger bun'], 'Avoid gluten-containing items'),
('dietary', 'keto', 'recommend', ARRAY['salad', 'chicken', 'fish', 'vegetables'], 'Focus on low-carb options'),

-- Allergies
('allergy', 'peanut', 'avoid', ARRAY['peanut', 'satay', 'thai'], 'Avoid peanut-based dishes'),
('allergy', 'shellfish', 'avoid', ARRAY['shrimp', 'crab', 'lobster', 'seafood'], 'Avoid shellfish dishes'),
('allergy', 'dairy', 'avoid', ARRAY['cheese', 'butter', 'cream', 'milk', 'dairy'], 'Avoid dairy products'),
('allergy', 'egg', 'avoid', ARRAY['egg', 'mayo', 'aioli'], 'Avoid egg-containing dishes'),
('allergy', 'nuts', 'avoid', ARRAY['nut', 'almond', 'cashew', 'walnut', 'pesto'], 'Avoid nut-based dishes'),

-- Illnesses (temporary conditions)
('illness', 'cough', 'recommend', ARRAY['soup', 'warm', 'herbal tea', 'ginger'], 'Warm soups and soothing foods recommended'),
('illness', 'flu', 'recommend', ARRAY['soup', 'warm', 'chicken soup', 'comfort food'], 'Comfort foods and warm meals recommended'),
('illness', 'nausea', 'caution', ARRAY['spicy', 'fried', 'heavy'], 'Avoid heavy, fried, or spicy foods'),
('illness', 'cold', 'recommend', ARRAY['soup', 'warm', 'vitamin-c', 'citrus'], 'Warm foods and vitamin-rich options'),

-- Digestive issues
('illness', 'indigestion', 'avoid', ARRAY['spicy', 'acidic', 'fried'], 'Avoid spicy, fried, or acidic foods'),
('illness', 'constipation', 'recommend', ARRAY['fiber', 'vegetables', 'fruits', 'water'], 'High-fiber options recommended');

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_health_conditions_updated_at BEFORE UPDATE ON public.health_conditions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON public.users TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.health_conditions TO authenticated;
GRANT SELECT, INSERT ON public.ocr_results TO authenticated;
GRANT SELECT ON public.menu_suggestions TO authenticated;

-- Supabase Database Schema for Dishes and Ingredients
-- Run this in your Supabase SQL editor after the main schema

-- Dishes table
CREATE TABLE IF NOT EXISTS public.dishes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name_original TEXT NOT NULL,
    name_english TEXT NOT NULL,
    description TEXT,
    category TEXT,
    price_range TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(name_english)
);

-- Ingredients table
CREATE TABLE IF NOT EXISTS public.ingredients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    allergen_info TEXT,
    dietary_info TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Dish Ingredients junction table
CREATE TABLE IF NOT EXISTS public.dish_ingredients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dish_id UUID REFERENCES public.dishes(id) ON DELETE CASCADE NOT NULL,
    ingredient_id UUID REFERENCES public.ingredients(id) ON DELETE CASCADE NOT NULL,
    quantity TEXT,
    is_main_ingredient BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(dish_id, ingredient_id)
);

-- Health condition dish recommendations
CREATE TABLE IF NOT EXISTS public.health_dish_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    condition_name TEXT NOT NULL,
    dish_id UUID REFERENCES public.dishes(id) ON DELETE CASCADE NOT NULL,
    recommendation_type TEXT NOT NULL CHECK (recommendation_type IN ('recommended', 'not_recommended', 'caution')),
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(condition_name, dish_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_dishes_name_english ON public.dishes(name_english);
CREATE INDEX IF NOT EXISTS idx_dish_ingredients_dish_id ON public.dish_ingredients(dish_id);
CREATE INDEX IF NOT EXISTS idx_dish_ingredients_ingredient_id ON public.dish_ingredients(ingredient_id);
CREATE INDEX IF NOT EXISTS idx_health_dish_recommendations_condition ON public.health_dish_recommendations(condition_name);
CREATE INDEX IF NOT EXISTS idx_health_dish_recommendations_dish ON public.health_dish_recommendations(dish_id);

-- Enable Row Level Security
ALTER TABLE public.dishes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ingredients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dish_ingredients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.health_dish_recommendations ENABLE ROW LEVEL SECURITY;

-- RLS Policies - Allow public read, authenticated write
CREATE POLICY "Anyone can view dishes" ON public.dishes FOR SELECT USING (true);
CREATE POLICY "Authenticated users can insert dishes" ON public.dishes FOR INSERT WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "Authenticated users can update dishes" ON public.dishes FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "Anyone can view ingredients" ON public.ingredients FOR SELECT USING (true);
CREATE POLICY "Authenticated users can insert ingredients" ON public.ingredients FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Anyone can view dish ingredients" ON public.dish_ingredients FOR SELECT USING (true);
CREATE POLICY "Authenticated users can manage dish ingredients" ON public.dish_ingredients FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Anyone can view health recommendations" ON public.health_dish_recommendations FOR SELECT USING (true);
CREATE POLICY "Authenticated users can manage recommendations" ON public.health_dish_recommendations FOR ALL USING (auth.role() = 'authenticated');

-- Function to update updated_at timestamp
CREATE TRIGGER update_dishes_updated_at BEFORE UPDATE ON public.dishes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions
GRANT SELECT ON public.dishes TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.dishes TO authenticated;
GRANT SELECT ON public.ingredients TO anon, authenticated;
GRANT SELECT, INSERT ON public.ingredients TO authenticated;
GRANT SELECT ON public.dish_ingredients TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.dish_ingredients TO authenticated;
GRANT SELECT ON public.health_dish_recommendations TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.health_dish_recommendations TO authenticated;

-- Insert sample data
INSERT INTO public.ingredients (name, allergen_info, dietary_info) VALUES
('Chicken', NULL, 'meat'),
('Beef', NULL, 'meat'),
('Fish', 'shellfish', 'meat'),
('Tomato', NULL, 'vegetable'),
('Cheese', 'dairy', 'dairy'),
('Milk', 'dairy', 'dairy'),
('Bread', 'gluten', 'grain'),
('Rice', NULL, 'grain'),
('Garlic', NULL, 'vegetable'),
('Onion', NULL, 'vegetable'),
('Spices', NULL, NULL),
('Oil', NULL, NULL),
('Butter', 'dairy', 'dairy'),
('Eggs', 'eggs', NULL),
('Nuts', 'nuts', NULL);

-- Insert sample dishes
INSERT INTO public.dishes (name_original, name_english, description, category, price_range) VALUES
('Poulet Grillé', 'Grilled Chicken', 'Tender grilled chicken with herbs', 'Main Course', '$15-20'),
('Salade César', 'Caesar Salad', 'Fresh romaine lettuce with Caesar dressing', 'Salad', '$10-15'),
('Soupe à l''oignon', 'Onion Soup', 'French onion soup with cheese', 'Soup', '$8-12'),
('Pasta Carbonara', 'Pasta Carbonara', 'Creamy pasta with bacon and eggs', 'Main Course', '$16-22'),
('Bouillabaisse', 'Seafood Stew', 'Traditional fish stew with vegetables', 'Soup', '$25-30'),
('Salade de Fruits', 'Fruit Salad', 'Fresh mixed seasonal fruits', 'Dessert', '$8-10');

-- Link dishes to ingredients
INSERT INTO public.dish_ingredients (dish_id, ingredient_id, is_main_ingredient)
SELECT d.id, i.id, true
FROM public.dishes d, public.ingredients i
WHERE (d.name_english = 'Grilled Chicken' AND i.name = 'Chicken')
   OR (d.name_english = 'Caesar Salad' AND i.name = 'Cheese')
   OR (d.name_english = 'Onion Soup' AND i.name = 'Cheese')
   OR (d.name_english = 'Pasta Carbonara' AND i.name = 'Eggs')
   OR (d.name_english = 'Seafood Stew' AND i.name = 'Fish');

-- Health condition recommendations
-- Fever/GI symptoms - not recommended
INSERT INTO public.health_dish_recommendations (condition_name, dish_id, recommendation_type, reason)
SELECT 'fever', d.id, 'not_recommended', 'Heavy/spicy foods can worsen fever symptoms'
FROM public.dishes d
WHERE d.name_english IN ('Pasta Carbonara', 'Seafood Stew', 'Grilled Chicken');

INSERT INTO public.health_dish_recommendations (condition_name, dish_id, recommendation_type, reason)
SELECT 'gastrointestinal', d.id, 'not_recommended', 'May cause digestive discomfort'
FROM public.dishes d
WHERE d.name_english IN ('Pasta Carbonara', 'Seafood Stew');

-- Fever/GI symptoms - recommended
INSERT INTO public.health_dish_recommendations (condition_name, dish_id, recommendation_type, reason)
SELECT 'fever', d.id, 'recommended', 'Light and easy to digest'
FROM public.dishes d
WHERE d.name_english IN ('Caesar Salad', 'Onion Soup', 'Fruit Salad');

INSERT INTO public.health_dish_recommendations (condition_name, dish_id, recommendation_type, reason)
SELECT 'gastrointestinal', d.id, 'recommended', 'Gentle on the stomach'
FROM public.dishes d
WHERE d.name_english IN ('Caesar Salad', 'Fruit Salad', 'Onion Soup');

