-- Execute this SQL in your Supabase SQL Editor to apply the enhanced schema

-- Enhanced dishes table with AI analysis
ALTER TABLE public.dishes ADD COLUMN IF NOT EXISTS is_vegetarian BOOLEAN DEFAULT FALSE;
ALTER TABLE public.dishes ADD COLUMN IF NOT EXISTS is_vegan BOOLEAN DEFAULT FALSE;
ALTER TABLE public.dishes ADD COLUMN IF NOT EXISTS is_non_veg BOOLEAN DEFAULT FALSE;
ALTER TABLE public.dishes ADD COLUMN IF NOT EXISTS dietary_tags TEXT[] DEFAULT '{}';
ALTER TABLE public.dishes ADD COLUMN IF NOT EXISTS cuisine_type TEXT DEFAULT 'General';
ALTER TABLE public.dishes ADD COLUMN IF NOT EXISTS spice_level INTEGER DEFAULT 0;
ALTER TABLE public.dishes ADD COLUMN IF NOT EXISTS meal_type TEXT DEFAULT 'Main Course';

-- Enhanced ingredients table with AI enrichment
ALTER TABLE public.ingredients ADD COLUMN IF NOT EXISTS ingredient_type TEXT;
ALTER TABLE public.ingredients ADD COLUMN IF NOT EXISTS calorie_per_100g INTEGER;
ALTER TABLE public.ingredients ADD COLUMN IF NOT EXISTS protein_content DECIMAL;
ALTER TABLE public.ingredients ADD COLUMN IF NOT EXISTS carb_content DECIMAL;
ALTER TABLE public.ingredients ADD COLUMN IF NOT EXISTS fat_content DECIMAL;

-- Similar dishes table for KNN recommendations
CREATE TABLE IF NOT EXISTS public.similar_dishes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dish_id UUID REFERENCES public.dishes(id) ON DELETE CASCADE NOT NULL,
    similar_dish_id UUID REFERENCES public.dishes(id) ON DELETE CASCADE NOT NULL,
    similarity_score DECIMAL(3,2) NOT NULL CHECK (similarity_score >= 0 AND similarity_score <= 1),
    category_type TEXT NOT NULL CHECK (category_type IN ('Mexican', 'European', 'General')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(dish_id, similar_dish_id, category_type)
);

-- AI Analysis results table
CREATE TABLE IF NOT EXISTS public.ai_analysis_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dish_id UUID REFERENCES public.dishes(id) ON DELETE CASCADE NOT NULL,
    analysis_type TEXT NOT NULL CHECK (analysis_type IN ('ingredients', 'dietary', 'similarity', 'full')),
    ollama_model TEXT,
    raw_analysis JSONB,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(dish_id, analysis_type)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_dishes_dietary ON public.dishes USING GIN (dietary_tags);
CREATE INDEX IF NOT EXISTS idx_dishes_cuisine ON public.dishes(cuisine_type);
CREATE INDEX IF NOT EXISTS idx_similar_dishes_dish_id ON public.similar_dishes(dish_id);
CREATE INDEX IF NOT EXISTS idx_similar_dishes_category ON public.similar_dishes(category_type);
CREATE INDEX IF NOT EXISTS idx_ai_analysis_dish_id ON public.ai_analysis_results(dish_id);

-- Enable RLS
ALTER TABLE public.similar_dishes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_analysis_results ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Anyone can view similar dishes" ON public.similar_dishes FOR SELECT USING (true);
CREATE POLICY "Authenticated users can manage similar dishes" ON public.similar_dishes FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Anyone can view AI analysis" ON public.ai_analysis_results FOR SELECT USING (true);
CREATE POLICY "Authenticated users can manage AI analysis" ON public.ai_analysis_results FOR ALL USING (auth.role() = 'authenticated');

-- Grant permissions
GRANT SELECT ON public.similar_dishes TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.similar_dishes TO authenticated;
GRANT SELECT ON public.ai_analysis_results TO anon, authenticated;
GRANT SELECT, INSERT ON public.ai_analysis_results TO authenticated;

-- Function to calculate similarity between dishes
CREATE OR REPLACE FUNCTION calculate_dish_similarity(dish1_id UUID, dish2_id UUID)
RETURNS DECIMAL(3,2) AS $$
DECLARE
    common_ingredients INTEGER;
    total_ingredients INTEGER;
    cuisine_match BOOLEAN;
    dietary_match BOOLEAN;
    final_similarity DECIMAL(3,2);
BEGIN
    -- Count common ingredients
    SELECT COUNT(*)
    INTO common_ingredients
    FROM dish_ingredients di1
    JOIN dish_ingredients di2 ON di1.ingredient_id = di2.ingredient_id
    WHERE di1.dish_id = dish1_id AND di2.dish_id = dish2_id;
    
    -- Get total unique ingredients for both dishes
    SELECT COUNT(DISTINCT ingredient_id)
    INTO total_ingredients
    FROM dish_ingredients
    WHERE dish_id IN (dish1_id, dish2_id);
    
    -- Check cuisine match
    SELECT (d1.cuisine_type = d2.cuisine_type)
    INTO cuisine_match
    FROM dishes d1, dishes d2
    WHERE d1.id = dish1_id AND d2.id = dish2_id;
    
    -- Check dietary compatibility
    SELECT (
        (d1.is_vegetarian = d2.is_vegetarian OR d2.is_vegetarian = FALSE) OR
        (d1.is_vegan = d2.is_vegan OR d2.is_vegan = FALSE) OR
        (d1.is_non_veg = d2.is_non_veg OR d2.is_non_veg = FALSE)
    )
    INTO dietary_match
    FROM dishes d1, dishes d2
    WHERE d1.id = dish1_id AND d2.id = dish2_id;
    
    -- Calculate final similarity score (0.0 to 1.0)
    final_similarity := 0.0;
    
    IF total_ingredients > 0 THEN
        final_similarity := final_similarity + (common_ingredients::DECIMAL / total_ingredients::DECIMAL) * 0.6;
    END IF;
    
    IF cuisine_match = TRUE THEN
        final_similarity := final_similarity + 0.2;
    END IF;
    
    IF dietary_match = TRUE THEN
        final_similarity := final_similarity + 0.2;
    END IF;
    
    RETURN LEAST(final_similarity, 1.0);
END;
$$ LANGUAGE plpgsql;