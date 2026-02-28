CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT UNIQUE,
  country TEXT DEFAULT 'IN',
  subscription TEXT DEFAULT 'free',
  subscription_plan TEXT DEFAULT 'free',
  premium_member BOOLEAN DEFAULT FALSE,
  premium_expires_at TIMESTAMPTZ,
  password_hash TEXT,
  auth_provider TEXT DEFAULT 'supabase',
  display_name TEXT,
  phone TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS email TEXT,
  ADD COLUMN IF NOT EXISTS country TEXT DEFAULT 'IN',
  ADD COLUMN IF NOT EXISTS subscription TEXT DEFAULT 'free',
  ADD COLUMN IF NOT EXISTS subscription_plan TEXT DEFAULT 'free',
  ADD COLUMN IF NOT EXISTS premium_member BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS premium_expires_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS password_hash TEXT,
  ADD COLUMN IF NOT EXISTS auth_provider TEXT DEFAULT 'supabase',
  ADD COLUMN IF NOT EXISTS display_name TEXT,
  ADD COLUMN IF NOT EXISTS phone TEXT,
  ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();

CREATE TABLE IF NOT EXISTS user_health_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  health_conditions TEXT[],
  allergies TEXT[],
  dietary_preferences TEXT[],
  medical_notes TEXT,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE user_health_profiles
  ADD COLUMN IF NOT EXISTS user_id UUID UNIQUE,
  ADD COLUMN IF NOT EXISTS health_conditions TEXT[],
  ADD COLUMN IF NOT EXISTS allergies TEXT[],
  ADD COLUMN IF NOT EXISTS dietary_preferences TEXT[],
  ADD COLUMN IF NOT EXISTS medical_notes TEXT,
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

CREATE TABLE IF NOT EXISTS menus (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id),
  restaurant_name TEXT,
  region TEXT,
  cuisine_type TEXT,
  r2_image_keys JSONB,
  ocr_raw TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, restaurant_name, region)
);

CREATE UNIQUE INDEX IF NOT EXISTS menus_user_restaurant_region_uidx
  ON menus(user_id, restaurant_name, region);

ALTER TABLE menus
  ADD COLUMN IF NOT EXISTS user_id UUID,
  ADD COLUMN IF NOT EXISTS restaurant_name TEXT,
  ADD COLUMN IF NOT EXISTS region TEXT,
  ADD COLUMN IF NOT EXISTS cuisine_type TEXT,
  ADD COLUMN IF NOT EXISTS r2_image_keys JSONB,
  ADD COLUMN IF NOT EXISTS ocr_raw TEXT,
  ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();

CREATE TABLE IF NOT EXISTS dishes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  menu_id UUID REFERENCES menus(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id),
  name TEXT NOT NULL,
  description TEXT,
  price DECIMAL(10, 2),
  currency TEXT DEFAULT 'EUR',
  category TEXT,
  ingredients_raw TEXT,
  ingredients_json JSONB,
  calories INT,
  protein_g DECIMAL(5, 2),
  fat_g DECIMAL(5, 2),
  carbs_g DECIMAL(5, 2),
  fiber_g DECIMAL(5, 2),
  sugar_g DECIMAL(5, 2),
  sodium_mg INT,
  cholesterol_mg INT,
  is_vegetarian BOOLEAN,
  is_vegan BOOLEAN,
  contains_dairy BOOLEAN,
  contains_gluten BOOLEAN,
  contains_nuts BOOLEAN,
  contains_shellfish BOOLEAN,
  health_score DECIMAL(3, 2),
  embedding VECTOR(1536),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE dishes
  ADD COLUMN IF NOT EXISTS menu_id UUID,
  ADD COLUMN IF NOT EXISTS user_id UUID,
  ADD COLUMN IF NOT EXISTS name TEXT,
  ADD COLUMN IF NOT EXISTS description TEXT,
  ADD COLUMN IF NOT EXISTS price DECIMAL(10, 2),
  ADD COLUMN IF NOT EXISTS currency TEXT DEFAULT 'EUR',
  ADD COLUMN IF NOT EXISTS category TEXT,
  ADD COLUMN IF NOT EXISTS ingredients_raw TEXT,
  ADD COLUMN IF NOT EXISTS ingredients_json JSONB,
  ADD COLUMN IF NOT EXISTS calories INT,
  ADD COLUMN IF NOT EXISTS protein_g DECIMAL(5, 2),
  ADD COLUMN IF NOT EXISTS fat_g DECIMAL(5, 2),
  ADD COLUMN IF NOT EXISTS carbs_g DECIMAL(5, 2),
  ADD COLUMN IF NOT EXISTS fiber_g DECIMAL(5, 2),
  ADD COLUMN IF NOT EXISTS sugar_g DECIMAL(5, 2),
  ADD COLUMN IF NOT EXISTS sodium_mg INT,
  ADD COLUMN IF NOT EXISTS cholesterol_mg INT,
  ADD COLUMN IF NOT EXISTS is_vegetarian BOOLEAN,
  ADD COLUMN IF NOT EXISTS is_vegan BOOLEAN,
  ADD COLUMN IF NOT EXISTS contains_dairy BOOLEAN,
  ADD COLUMN IF NOT EXISTS contains_gluten BOOLEAN,
  ADD COLUMN IF NOT EXISTS contains_nuts BOOLEAN,
  ADD COLUMN IF NOT EXISTS contains_shellfish BOOLEAN,
  ADD COLUMN IF NOT EXISTS health_score DECIMAL(3, 2),
  ADD COLUMN IF NOT EXISTS embedding VECTOR(1536),
  ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();

CREATE TABLE IF NOT EXISTS dish_health_recommendations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  dish_id UUID REFERENCES dishes(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  recommendation_level TEXT,
  risk_summary TEXT,
  trigger_ingredients JSONB,
  alternative_suggestion TEXT,
  alternative_dish_name TEXT,
  triggered_health_conditions TEXT[],
  gemini_analysis JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(dish_id, user_id)
);

ALTER TABLE dish_health_recommendations
  ADD COLUMN IF NOT EXISTS dish_id UUID,
  ADD COLUMN IF NOT EXISTS user_id UUID,
  ADD COLUMN IF NOT EXISTS recommendation_level TEXT,
  ADD COLUMN IF NOT EXISTS risk_summary TEXT,
  ADD COLUMN IF NOT EXISTS trigger_ingredients JSONB,
  ADD COLUMN IF NOT EXISTS alternative_suggestion TEXT,
  ADD COLUMN IF NOT EXISTS alternative_dish_name TEXT,
  ADD COLUMN IF NOT EXISTS triggered_health_conditions TEXT[],
  ADD COLUMN IF NOT EXISTS gemini_analysis JSONB,
  ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();

CREATE TABLE IF NOT EXISTS jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id),
  status TEXT DEFAULT 'queued',
  r2_keys JSONB,
  target_lang TEXT DEFAULT 'en',
  user_country TEXT DEFAULT 'IN',
  error TEXT,
  menu_id UUID,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE jobs
  ADD COLUMN IF NOT EXISTS user_id UUID,
  ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'queued',
  ADD COLUMN IF NOT EXISTS r2_keys JSONB,
  ADD COLUMN IF NOT EXISTS target_lang TEXT DEFAULT 'en',
  ADD COLUMN IF NOT EXISTS user_country TEXT DEFAULT 'IN',
  ADD COLUMN IF NOT EXISTS error TEXT,
  ADD COLUMN IF NOT EXISTS menu_id UUID,
  ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW(),
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_dishes_menu_id ON dishes(menu_id);
CREATE INDEX IF NOT EXISTS idx_dishes_embedding ON dishes USING ivfflat(embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_recommendations_user ON dish_health_recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_dish ON dish_health_recommendations(dish_id);
CREATE INDEX IF NOT EXISTS idx_health_profiles_user ON user_health_profiles(user_id);

ALTER TABLE user_health_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE dishes ENABLE ROW LEVEL SECURITY;
ALTER TABLE dish_health_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE menus ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'jobs' AND policyname = 'user_own_jobs'
  ) THEN
    CREATE POLICY "user_own_jobs" ON jobs
      FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'menus' AND policyname = 'user_own_menus'
  ) THEN
    CREATE POLICY "user_own_menus" ON menus
      FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'user_health_profiles' AND policyname = 'user_own_health_profile'
  ) THEN
    CREATE POLICY "user_own_health_profile" ON user_health_profiles
      FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'dishes' AND policyname = 'user_own_dishes'
  ) THEN
    CREATE POLICY "user_own_dishes" ON dishes
      FOR SELECT USING (user_id = auth.uid());
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'dish_health_recommendations' AND policyname = 'user_own_recommendations'
  ) THEN
    CREATE POLICY "user_own_recommendations" ON dish_health_recommendations
      FOR SELECT USING (user_id = auth.uid());
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'users' AND policyname = 'user_own_users'
  ) THEN
    CREATE POLICY "user_own_users" ON users
      FOR SELECT USING (id = auth.uid());
  END IF;
END $$;

CREATE OR REPLACE FUNCTION get_personalized_menu(p_menu_id UUID, p_user_id UUID)
RETURNS TABLE(
  dish_id UUID,
  dish_name TEXT,
  price DECIMAL,
  ingredients TEXT,
  calories INT,
  recommendation_level TEXT,
  risk_summary TEXT,
  trigger_ingredients JSONB,
  alternative_suggestion TEXT,
  health_score DECIMAL
) AS $$
SELECT
  d.id,
  d.name,
  d.price,
  d.ingredients_raw,
  d.calories,
  COALESCE(dhr.recommendation_level, 'unknown'),
  COALESCE(dhr.risk_summary, 'No health risks detected'),
  COALESCE(dhr.trigger_ingredients, '[]'::JSONB),
  COALESCE(dhr.alternative_suggestion, NULL),
  d.health_score
FROM dishes d
LEFT JOIN dish_health_recommendations dhr ON d.id = dhr.dish_id AND dhr.user_id = p_user_id
WHERE d.menu_id = p_menu_id
ORDER BY CASE
  WHEN dhr.recommendation_level = 'avoid' THEN 1
  WHEN dhr.recommendation_level = 'caution' THEN 2
  WHEN dhr.recommendation_level = 'safe' THEN 3
  ELSE 4
END;
$$ LANGUAGE sql;
