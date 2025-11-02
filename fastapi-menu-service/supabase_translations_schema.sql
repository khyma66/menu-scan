-- Translations table for storing OCR text translations
-- This stores translations from detected languages to English

CREATE TABLE IF NOT EXISTS translations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    original_text TEXT NOT NULL,
    original_language VARCHAR(10) NOT NULL, -- Language code (e.g., 'fr', 'es', 'de')
    translated_text TEXT NOT NULL,
    translation_method VARCHAR(50) DEFAULT 'dish_database', -- 'dish_database', 'llm', 'manual'
    context TEXT, -- Additional context (e.g., 'menu_item', 'description')
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE, -- Optional: track which user made the translation
    usage_count INTEGER DEFAULT 1, -- How many times this translation was used
    
    -- Indexes for faster lookups
    CONSTRAINT translations_original_text_lang_unique UNIQUE (original_text, original_language)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_translations_original_text ON translations(original_text);
CREATE INDEX IF NOT EXISTS idx_translations_original_language ON translations(original_language);
CREATE INDEX IF NOT EXISTS idx_translations_translated_text ON translations(translated_text);
CREATE INDEX IF NOT EXISTS idx_translations_user_id ON translations(user_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_translations_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
CREATE TRIGGER trigger_update_translations_updated_at
    BEFORE UPDATE ON translations
    FOR EACH ROW
    EXECUTE FUNCTION update_translations_updated_at();

-- RLS Policies
ALTER TABLE translations ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read all translations (public translations)
CREATE POLICY "Translations are readable by everyone"
    ON translations FOR SELECT
    USING (true);

-- Policy: Authenticated users can insert translations
CREATE POLICY "Authenticated users can create translations"
    ON translations FOR INSERT
    WITH CHECK (auth.role() = 'authenticated' OR user_id IS NULL);

-- Policy: Service role can do everything
CREATE POLICY "Service role has full access"
    ON translations FOR ALL
    USING (auth.role() = 'service_role');

-- Function to increment usage count or insert new translation
CREATE OR REPLACE FUNCTION upsert_translation(
    p_original_text TEXT,
    p_original_language VARCHAR(10),
    p_translated_text TEXT,
    p_translation_method VARCHAR(50) DEFAULT 'dish_database',
    p_context TEXT DEFAULT NULL,
    p_user_id UUID DEFAULT NULL
)
RETURNS translations AS $$
DECLARE
    v_result translations;
BEGIN
    INSERT INTO translations (
        original_text,
        original_language,
        translated_text,
        translation_method,
        context,
        user_id,
        usage_count
    )
    VALUES (
        p_original_text,
        p_original_language,
        p_translated_text,
        p_translation_method,
        p_context,
        p_user_id,
        1
    )
    ON CONFLICT (original_text, original_language)
    DO UPDATE SET
        translated_text = EXCLUDED.translated_text,
        translation_method = EXCLUDED.translation_method,
        context = EXCLUDED.context,
        usage_count = translations.usage_count + 1,
        updated_at = NOW()
    RETURNING * INTO v_result;
    
    RETURN v_result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

