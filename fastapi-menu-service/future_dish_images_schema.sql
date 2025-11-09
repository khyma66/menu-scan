-- Future Dish Images Storage Schema for Menu OCR
-- Plan for storing dish images in separate Supabase buckets with metadata

-- ============================================================================
-- DISH IMAGES STORAGE ARCHITECTURE
-- ============================================================================

-- 1. Supabase Storage Buckets Structure
-- =====================================
-- Bucket: dish-images-{restaurant_id}
--   - Organized by restaurant for better management
--   - Separate buckets prevent cross-contamination
--   - Easier permission management per restaurant

-- Bucket: user-uploaded-menus
--   - Original menu photos uploaded by users
--   - OCR processing results stored as metadata

-- Bucket: processed-dishes
--   - AI-generated or enhanced dish images
--   - Cropped portions from menu photos

-- 2. Database Tables for Image Metadata
-- =====================================

-- Restaurant-specific dish images
CREATE TABLE IF NOT EXISTS public.dish_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dish_name TEXT NOT NULL,
    restaurant_name TEXT,
    restaurant_id UUID, -- Links to restaurant table when implemented

    -- Image storage info
    bucket_name TEXT NOT NULL, -- e.g., 'dish-images-marios-italian'
    image_path TEXT NOT NULL, -- Full path in Supabase storage
    image_url TEXT NOT NULL, -- Public URL for access
    thumbnail_url TEXT, -- Smaller version for lists

    -- Image metadata
    image_width INTEGER,
    image_height INTEGER,
    file_size_bytes INTEGER,
    content_type TEXT DEFAULT 'image/jpeg',
    uploaded_by UUID REFERENCES auth.users(id),

    -- Dish identification
    menu_item_id UUID, -- Links to processed menu items
    ingredient_match_score DECIMAL(3,2), -- How well image matches dish
    ai_generated BOOLEAN DEFAULT false, -- True if AI-created image

    -- Quality and processing info
    image_quality_score DECIMAL(3,2), -- 0.0 to 1.0
    processing_status TEXT DEFAULT 'pending', -- pending, processing, completed, failed
    ocr_confidence DECIMAL(3,2),
    last_processed_at TIMESTAMP WITH TIME ZONE,

    -- Categorization
    cuisine_type TEXT, -- italian, chinese, mexican, etc.
    dish_category TEXT, -- appetizer, main, dessert, drink
    dietary_tags TEXT[], -- vegetarian, vegan, gluten-free, etc.

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User uploaded menu images (source images)
CREATE TABLE IF NOT EXISTS public.menu_uploads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Original image info
    original_filename TEXT NOT NULL,
    bucket_name TEXT DEFAULT 'user-uploaded-menus',
    image_path TEXT NOT NULL,
    image_url TEXT NOT NULL,

    -- Processing status
    processing_status TEXT DEFAULT 'uploaded', -- uploaded, ocr_processing, menu_extracted, completed
    ocr_text TEXT, -- Raw OCR text
    extracted_menu_data JSONB, -- Processed menu data

    -- Metadata
    image_width INTEGER,
    image_height INTEGER,
    file_size_bytes INTEGER,
    device_info JSONB, -- Camera, OS version, etc.

    -- Restaurant detection
    detected_restaurant_name TEXT,
    detected_cuisine_type TEXT,
    confidence_score DECIMAL(3,2),

    -- Processing timestamps
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ocr_completed_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,

    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3
);

-- Link between menu uploads and extracted dishes
CREATE TABLE IF NOT EXISTS public.upload_dish_mapping (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    upload_id UUID REFERENCES public.menu_uploads(id) ON DELETE CASCADE,
    dish_name TEXT NOT NULL,
    dish_image_id UUID REFERENCES public.dish_images(id),

    -- Extraction details
    bounding_box JSONB, -- Coordinates where dish was found in image
    confidence_score DECIMAL(3,2),
    extracted_price DECIMAL(8,2),
    extracted_description TEXT,

    -- Processing metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_dish_images_dish_name ON public.dish_images USING gin(dish_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_dish_images_restaurant ON public.dish_images(restaurant_name);
CREATE INDEX IF NOT EXISTS idx_dish_images_cuisine ON public.dish_images(cuisine_type);
CREATE INDEX IF NOT EXISTS idx_dish_images_category ON public.dish_images(dish_category);
CREATE INDEX IF NOT EXISTS idx_dish_images_uploaded_by ON public.dish_images(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_dish_images_menu_item ON public.dish_images(menu_item_id);

CREATE INDEX IF NOT EXISTS idx_menu_uploads_user ON public.menu_uploads(user_id);
CREATE INDEX IF NOT EXISTS idx_menu_uploads_status ON public.menu_uploads(processing_status);
CREATE INDEX IF NOT EXISTS idx_menu_uploads_restaurant ON public.menu_uploads(detected_restaurant_name);

CREATE INDEX IF NOT EXISTS idx_upload_dish_mapping_upload ON public.upload_dish_mapping(upload_id);
CREATE INDEX IF NOT EXISTS idx_upload_dish_mapping_dish ON public.upload_dish_mapping(dish_name);

-- ============================================================================
-- ROW LEVEL SECURITY POLICIES
-- ============================================================================

ALTER TABLE public.dish_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.menu_uploads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.upload_dish_mapping ENABLE ROW LEVEL SECURITY;

-- Dish images: readable by all authenticated users
CREATE POLICY "Dish images are viewable by authenticated users"
    ON public.dish_images FOR SELECT
    USING (auth.role() = 'authenticated');

-- Menu uploads: users can only see their own uploads
CREATE POLICY "Users can view their own menu uploads"
    ON public.menu_uploads FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own menu uploads"
    ON public.menu_uploads FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own menu uploads"
    ON public.menu_uploads FOR UPDATE
    USING (auth.uid() = user_id);

-- Upload dish mappings: accessible through upload permissions
CREATE POLICY "Upload dish mappings accessible via uploads"
    ON public.upload_dish_mapping FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.menu_uploads
            WHERE id = upload_dish_mapping.upload_id
            AND user_id = auth.uid()
        )
    );

-- ============================================================================
-- UTILITY FUNCTIONS
-- ============================================================================

-- Function to get dish images for a restaurant
CREATE OR REPLACE FUNCTION get_restaurant_dish_images(restaurant_name_param TEXT)
RETURNS TABLE (
    dish_name TEXT,
    image_url TEXT,
    thumbnail_url TEXT,
    dish_category TEXT,
    dietary_tags TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        di.dish_name,
        di.image_url,
        di.thumbnail_url,
        di.dish_category,
        di.dietary_tags
    FROM dish_images di
    WHERE di.restaurant_name = restaurant_name_param
    ORDER BY di.dish_name;
END;
$$ LANGUAGE plpgsql;

-- Function to get user's recent menu uploads
CREATE OR REPLACE FUNCTION get_user_menu_uploads(user_id_param UUID, limit_count INTEGER DEFAULT 10)
RETURNS TABLE (
    id UUID,
    filename TEXT,
    status TEXT,
    uploaded_at TIMESTAMP WITH TIME ZONE,
    restaurant_name TEXT,
    dish_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        mu.id,
        mu.original_filename,
        mu.processing_status,
        mu.uploaded_at,
        mu.detected_restaurant_name,
        COUNT(udm.id)::INTEGER as dish_count
    FROM menu_uploads mu
    LEFT JOIN upload_dish_mapping udm ON mu.id = udm.upload_id
    WHERE mu.user_id = user_id_param
    GROUP BY mu.id, mu.original_filename, mu.processing_status, mu.uploaded_at, mu.detected_restaurant_name
    ORDER BY mu.uploaded_at DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Function to find similar dishes by image analysis
CREATE OR REPLACE FUNCTION find_similar_dishes(search_dish_name TEXT, cuisine_filter TEXT DEFAULT NULL)
RETURNS TABLE (
    dish_name TEXT,
    restaurant_name TEXT,
    image_url TEXT,
    similarity_score DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        di.dish_name,
        di.restaurant_name,
        di.image_url,
        (1 - (di.dish_name <-> search_dish_name)) as similarity_score
    FROM dish_images di
    WHERE (cuisine_filter IS NULL OR di.cuisine_type = cuisine_filter)
    ORDER BY similarity_score DESC
    LIMIT 5;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- STORAGE BUCKET POLICIES (TO BE IMPLEMENTED IN SUPABASE DASHBOARD)
-- ============================================================================

/*
Storage Bucket Policies to implement in Supabase Dashboard:

1. dish-images-{restaurant_id} bucket:
   - Allow authenticated users to view images
   - Allow restaurant owners to upload/manage their images
   - Public read access for web/mobile apps

2. user-uploaded-menus bucket:
   - Private bucket: only owners can access their uploads
   - Temporary signed URLs for processing
   - Automatic cleanup after processing

3. processed-dishes bucket:
   - Public read access for all processed dish images
   - Authenticated users can upload (via backend processing)
   - CDN optimization for fast delivery
*/

-- ============================================================================
-- MIGRATION NOTES
-- ============================================================================

/*
Migration Path:
1. Create storage buckets in Supabase dashboard
2. Run this schema to create tables
3. Update backend services to use new image storage
4. Migrate existing dish data to new structure
5. Update mobile apps to handle image URLs
6. Implement image upload/processing workflows
7. Add image optimization and CDN setup
*/

-- Grant permissions
GRANT SELECT ON public.dish_images TO authenticated;
GRANT SELECT, INSERT, UPDATE ON public.menu_uploads TO authenticated;
GRANT SELECT ON public.upload_dish_mapping TO authenticated;

-- Updated at trigger
CREATE TRIGGER update_dish_images_updated_at BEFORE UPDATE ON public.dish_images
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_menu_uploads_updated_at BEFORE UPDATE ON public.menu_uploads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();