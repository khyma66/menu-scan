-- Additional SQL to ensure users are created in public.users table
-- Run this AFTER supabase_schema.sql

-- Function to automatically create user profile when auth.users is created
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (id, email, full_name)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email)
  )
  ON CONFLICT (id) DO UPDATE
  SET email = NEW.email,
      updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create user profile on signup
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- View to get user info with health conditions
CREATE OR REPLACE VIEW public.user_info_with_conditions AS
SELECT 
  u.id,
  u.email,
  u.full_name,
  u.phone,
  u.created_at,
  u.updated_at,
  COALESCE(
    json_agg(
      json_build_object(
        'id', hc.id,
        'condition_type', hc.condition_type,
        'condition_name', hc.condition_name,
        'severity', hc.severity,
        'description', hc.description,
        'created_at', hc.created_at
      )
    ) FILTER (WHERE hc.id IS NOT NULL),
    '[]'::json
  ) as health_conditions
FROM public.users u
LEFT JOIN public.health_conditions hc ON u.id = hc.user_id
GROUP BY u.id, u.email, u.full_name, u.phone, u.created_at, u.updated_at;

-- Grant permissions on view
GRANT SELECT ON public.user_info_with_conditions TO authenticated;

-- Update RLS to allow users to view their own info
ALTER VIEW public.user_info_with_conditions SET (security_invoker = true);

