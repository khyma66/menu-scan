-- New Health Recommendation System Schema
-- This replaces the problematic health_conditions table with a more robust design

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Health profiles table (independent of users table for reliability)
CREATE TABLE IF NOT EXISTS public.health_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL, -- No foreign key constraint to avoid failures
    profile_name TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Health conditions table (references health_profiles)
CREATE TABLE IF NOT EXISTS public.health_conditions_v2 (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID REFERENCES health_profiles(id) ON DELETE CASCADE,
    condition_type TEXT NOT NULL CHECK (condition_type IN ('allergy', 'illness', 'dietary', 'preference')),
    condition_name TEXT NOT NULL,
    severity TEXT CHECK (severity IN ('mild', 'moderate', 'severe')),
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB, -- Store additional condition data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Health recommendations cache table
CREATE TABLE IF NOT EXISTS public.health_recommendations_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    conditions_hash TEXT NOT NULL, -- Hash of user's conditions for cache invalidation
    recommendations JSONB,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Health analytics table
CREATE TABLE IF NOT EXISTS public.health_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    action TEXT NOT NULL, -- 'add_condition', 'remove_condition', 'get_recommendations', 'view_analytics'
    condition_type TEXT,
    condition_name TEXT,
    menu_item TEXT,
    recommendation TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_health_profiles_user_id ON public.health_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_health_profiles_active ON public.health_profiles(is_active);
CREATE INDEX IF NOT EXISTS idx_health_conditions_v2_profile_id ON public.health_conditions_v2(profile_id);
CREATE INDEX IF NOT EXISTS idx_health_conditions_v2_active ON public.health_conditions_v2(is_active);
CREATE INDEX IF NOT EXISTS idx_health_conditions_v2_type ON public.health_conditions_v2(condition_type);
CREATE INDEX IF NOT EXISTS idx_health_recommendations_cache_user ON public.health_recommendations_cache(user_id);
CREATE INDEX IF NOT EXISTS idx_health_recommendations_cache_hash ON public.health_recommendations_cache(conditions_hash);
CREATE INDEX IF NOT EXISTS idx_health_recommendations_cache_expires ON public.health_recommendations_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_health_analytics_user ON public.health_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_health_analytics_action ON public.health_analytics(action);

-- Row Level Security Policies
ALTER TABLE public.health_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.health_conditions_v2 ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.health_recommendations_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.health_analytics ENABLE ROW LEVEL SECURITY;

-- RLS Policies for health_profiles
CREATE POLICY "Users can view own health profiles"
    ON public.health_profiles FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own health profiles"
    ON public.health_profiles FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own health profiles"
    ON public.health_profiles FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own health profiles"
    ON public.health_profiles FOR DELETE
    USING (auth.uid() = user_id);

-- RLS Policies for health_conditions_v2
CREATE POLICY "Users can view own health conditions"
    ON public.health_conditions_v2 FOR SELECT
    USING (
        profile_id IN (
            SELECT id FROM public.health_profiles
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own health conditions"
    ON public.health_conditions_v2 FOR INSERT
    WITH CHECK (
        profile_id IN (
            SELECT id FROM public.health_profiles
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update own health conditions"
    ON public.health_conditions_v2 FOR UPDATE
    USING (
        profile_id IN (
            SELECT id FROM public.health_profiles
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete own health conditions"
    ON public.health_conditions_v2 FOR DELETE
    USING (
        profile_id IN (
            SELECT id FROM public.health_profiles
            WHERE user_id = auth.uid()
        )
    );

-- RLS Policies for health_recommendations_cache
CREATE POLICY "Users can view own cached recommendations"
    ON public.health_recommendations_cache FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own cached recommendations"
    ON public.health_recommendations_cache FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own cached recommendations"
    ON public.health_recommendations_cache FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own cached recommendations"
    ON public.health_recommendations_cache FOR DELETE
    USING (auth.uid() = user_id);

-- RLS Policies for health_analytics
CREATE POLICY "Users can view own analytics"
    ON public.health_analytics FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own analytics"
    ON public.health_analytics FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_health_profiles_updated_at
    BEFORE UPDATE ON public.health_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_health_conditions_v2_updated_at
    BEFORE UPDATE ON public.health_conditions_v2
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to generate conditions hash for caching
CREATE OR REPLACE FUNCTION generate_conditions_hash(user_conditions JSONB)
RETURNS TEXT AS $$
BEGIN
    RETURN encode(sha256(user_conditions::text::bytea), 'hex');
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON public.health_profiles TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.health_conditions_v2 TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.health_recommendations_cache TO authenticated;
GRANT SELECT, INSERT ON public.health_analytics TO authenticated;

-- Insert sample health conditions data
INSERT INTO public.health_profiles (user_id, profile_name) VALUES
('00000000-0000-0000-0000-000000000000', 'Default Profile')
ON CONFLICT DO NOTHING;

-- Insert sample conditions for testing
INSERT INTO public.health_conditions_v2 (profile_id, condition_type, condition_name, severity, description) VALUES
((SELECT id FROM public.health_profiles WHERE user_id = '00000000-0000-0000-0000-000000000000' LIMIT 1), 'allergy', 'peanut', 'severe', 'Severe peanut allergy'),
((SELECT id FROM public.health_profiles WHERE user_id = '00000000-0000-0000-0000-000000000000' LIMIT 1), 'allergy', 'shellfish', 'moderate', 'Moderate shellfish allergy'),
((SELECT id FROM public.health_profiles WHERE user_id = '00000000-0000-0000-0000-000000000000' LIMIT 1), 'dietary', 'vegetarian', NULL, 'Vegetarian diet'),
((SELECT id FROM public.health_profiles WHERE user_id = '00000000-0000-0000-0000-000000000000' LIMIT 1), 'illness', 'fever', 'mild', 'Currently has mild fever')
ON CONFLICT DO NOTHING;