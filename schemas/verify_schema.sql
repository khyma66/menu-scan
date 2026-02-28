-- Verification Query for Supabase Schema
-- Run this after running the schemas to verify everything is set up correctly

-- Check if tables exist
SELECT 
    table_name,
    CASE 
        WHEN table_name IN (
            'users',
            'health_conditions',
            'dishes',
            'ingredients',
            'dish_ingredients',
            'health_dish_recommendations',
            'ocr_results',
            'menu_suggestions',
            'user_profile_details',
            'user_profile_preferences',
            'user_health_preferences',
            'user_recent_scans',
            'user_scan_preferences',
            'user_saved_cards',
            'user_payment_history',
            'user_subscriptions',
            'user_discovery_preferences'
        ) 
        THEN '✅ Exists'
        ELSE '⚠️ Missing'
    END as status
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'users',
    'health_conditions',
    'dishes',
    'ingredients',
    'dish_ingredients',
    'health_dish_recommendations',
    'ocr_results',
    'menu_suggestions',
    'user_profile_details',
    'user_profile_preferences',
    'user_health_preferences',
    'user_recent_scans',
    'user_scan_preferences',
    'user_saved_cards',
    'user_payment_history',
    'user_subscriptions',
    'user_discovery_preferences'
)
ORDER BY table_name;

-- Check sample data
SELECT 'dishes' as table_name, COUNT(*) as count FROM public.dishes
UNION ALL
SELECT 'ingredients', COUNT(*) FROM public.ingredients
UNION ALL
SELECT 'menu_suggestions', COUNT(*) FROM public.menu_suggestions
UNION ALL
SELECT 'health_dish_recommendations', COUNT(*) FROM public.health_dish_recommendations
UNION ALL
SELECT 'user_profile_details', COUNT(*) FROM public.user_profile_details
UNION ALL
SELECT 'user_health_preferences', COUNT(*) FROM public.user_health_preferences
UNION ALL
SELECT 'user_recent_scans', COUNT(*) FROM public.user_recent_scans
UNION ALL
SELECT 'user_subscriptions', COUNT(*) FROM public.user_subscriptions;

