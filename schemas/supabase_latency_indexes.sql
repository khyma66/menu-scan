-- Supabase latency-focused indexes for frequently queried paths
-- Safe to run multiple times

create index if not exists idx_ocr_results_created_at_desc
  on public.ocr_results (created_at desc);

create index if not exists idx_ocr_results_user_created_at_desc
  on public.ocr_results (user_id, created_at desc);

create index if not exists idx_health_conditions_user_type
  on public.health_conditions (user_id, condition_type);

create index if not exists idx_health_conditions_user_name
  on public.health_conditions (user_id, condition_name);

create index if not exists idx_menu_restaurant_id
  on public.menu (restaurant_id);

create index if not exists idx_user_recent_scans_user_scanned_desc
  on public.user_recent_scans (user_id, scanned_at desc);

create index if not exists idx_user_payment_history_user_created_desc
  on public.user_payment_history (user_id, created_at desc);

create index if not exists idx_user_subscriptions_user_status
  on public.user_subscriptions (user_id, status);
