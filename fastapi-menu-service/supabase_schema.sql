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

