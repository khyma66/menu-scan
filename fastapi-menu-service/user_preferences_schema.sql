-- User Preferences Schema for Menu OCR
-- Run this in your Supabase SQL editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Food preferences table
CREATE TABLE IF NOT EXISTS public.food_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
    preference_type TEXT NOT NULL CHECK (preference_type IN ('favorite', 'disliked', 'neutral')),
    food_category TEXT NOT NULL, -- e.g., 'spicy', 'sweet', 'savory', 'italian', 'mexican'
    food_item TEXT, -- Specific food item, can be null for categories
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User preferences table (general profile preferences)
CREATE TABLE IF NOT EXISTS public.user_preferences (
    user_id UUID PRIMARY KEY REFERENCES public.users(id) ON DELETE CASCADE,
    dietary_restrictions TEXT[], -- Array of dietary restrictions
    favorite_cuisines TEXT[], -- Array of favorite cuisines
    spice_tolerance TEXT CHECK (spice_tolerance IN ('none', 'mild', 'medium', 'hot', 'very_hot')),
    budget_preference TEXT CHECK (budget_preference IN ('budget', 'moderate', 'premium')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_food_preferences_user_id ON public.food_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_food_preferences_category ON public.food_preferences(food_category);
CREATE INDEX IF NOT EXISTS idx_food_preferences_type ON public.food_preferences(preference_type);

-- Enable Row Level Security
ALTER TABLE public.food_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;

-- RLS Policies for food_preferences
CREATE POLICY "Users can view own food preferences"
    ON public.food_preferences FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own food preferences"
    ON public.food_preferences FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own food preferences"
    ON public.food_preferences FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own food preferences"
    ON public.food_preferences FOR DELETE
    USING (auth.uid() = user_id);

-- RLS Policies for user_preferences
CREATE POLICY "Users can view own preferences"
    ON public.user_preferences FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own preferences"
    ON public.user_preferences FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own preferences"
    ON public.user_preferences FOR UPDATE
    USING (auth.uid() = user_id);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_food_preferences_updated_at BEFORE UPDATE ON public.food_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON public.user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON public.food_preferences TO authenticated;
GRANT SELECT, INSERT, UPDATE ON public.user_preferences TO authenticated;

-- Insert sample food preferences data
INSERT INTO public.food_preferences (user_id, preference_type, food_category, food_item, rating, notes) VALUES
-- Sample preferences (these would be created by actual users)
-- Note: Replace with actual user_id when testing
-- ('user-uuid-here', 'favorite', 'italian', 'pizza', 5, 'Love the cheese and tomato sauce'),
-- ('user-uuid-here', 'disliked', 'spicy', 'hot wings', 1, 'Too spicy for me'),
-- ('user-uuid-here', 'favorite', 'sweet', 'chocolate cake', 5, 'Perfect dessert');

-- Insert sample user preferences
-- INSERT INTO public.user_preferences (user_id, dietary_restrictions, favorite_cuisines, spice_tolerance, budget_preference) VALUES
-- ('user-uuid-here', ARRAY['vegetarian'], ARRAY['italian', 'mexican'], 'mild', 'moderate');