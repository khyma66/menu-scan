-- Consolidated required schema for Menu OCR apps (Android + iOS)
-- Safe to run multiple times.

create extension if not exists "pgcrypto";
create extension if not exists "uuid-ossp";

create or replace function public.set_updated_at_timestamp()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- =========
-- Core user tables
-- =========
create table if not exists public.users (
  id uuid primary key references auth.users(id) on delete cascade,
  email text unique,
  full_name text,
  phone text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.user_profile_details (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  full_name text,
  email text,
  contact text,
  phone text,
  country text,
  avatar_url text,
  preferred_language text,
  timezone text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(user_id)
);

create table if not exists public.user_addresses (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  type text not null default 'home',
  street text not null,
  apartment_number text,
  city text not null,
  state text not null,
  zip_code text not null,
  country text not null default 'US',
  is_primary boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.user_profile_preferences (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  notifications_enabled boolean not null default true,
  notification_push_enabled boolean not null default true,
  notification_email_enabled boolean not null default true,
  privacy_profile_visibility text not null default 'private' check (privacy_profile_visibility in ('public','friends','private')),
  analytics_opt_in boolean not null default true,
  marketing_opt_in boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(user_id)
);

-- =========
-- Discover
-- =========
create table if not exists public.user_discovery_preferences (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  search_radius_miles int not null default 10,
  selected_cuisines text[] not null default '{}',
  location_label text,
  latitude double precision,
  longitude double precision,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(user_id)
);

-- =========
-- Health (compat + v2)
-- =========
create table if not exists public.user_health_preferences (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  health_conditions text[] not null default '{}',
  allergies text[] not null default '{}',
  dietary_preferences text[] not null default '{}',
  taste_preferences text[] not null default '{}',
  medical_notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(user_id)
);

create table if not exists public.health_conditions (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references auth.users(id) on delete cascade,
  condition_type text not null check (condition_type in ('allergy','illness','dietary','preference')),
  condition_name text not null,
  severity text check (severity in ('mild','moderate','severe')),
  description text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.health_profiles (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null,
  profile_name text,
  is_active boolean default true,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.health_conditions_v2 (
  id uuid primary key default uuid_generate_v4(),
  profile_id uuid references public.health_profiles(id) on delete cascade,
  condition_type text not null check (condition_type in ('allergy','illness','dietary','preference')),
  condition_name text not null,
  severity text check (severity in ('mild','moderate','severe')),
  description text,
  is_active boolean default true,
  metadata jsonb,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.health_recommendations_cache (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null,
  conditions_hash text not null,
  recommendations jsonb,
  expires_at timestamptz,
  created_at timestamptz default now(),
  unique(user_id, conditions_hash)
);

create table if not exists public.health_analytics (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null,
  action text not null,
  condition_type text,
  condition_name text,
  menu_item text,
  recommendation text,
  metadata jsonb,
  created_at timestamptz default now()
);

-- =========
-- OCR + scan history
-- =========
create table if not exists public.ocr_results (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references auth.users(id) on delete cascade,
  image_url text,
  result jsonb,
  processed_at timestamptz default now()
);

create table if not exists public.user_recent_scans (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  scanned_at timestamptz not null default now(),
  source text,
  image_name text,
  image_url text,
  detected_language text,
  output_language text,
  dish_count int,
  processing_status text default 'completed' check (processing_status in ('queued','processing','completed','failed')),
  processing_time_ms int,
  pipeline text,
  ocr_result_id uuid,
  created_at timestamptz not null default now()
);

create table if not exists public.user_scan_preferences (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  default_source text not null default 'camera' check (default_source in ('camera','gallery')),
  auto_translate boolean not null default false,
  translate_language text,
  save_scan_history boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(user_id)
);

-- =========
-- Profile preferences
-- =========
create table if not exists public.user_preferences (
  user_id uuid primary key references auth.users(id) on delete cascade,
  dietary_restrictions text[] default '{}',
  favorite_cuisines text[] default '{}',
  spice_tolerance text check (spice_tolerance in ('none','mild','medium','hot','very_hot')),
  budget_preference text check (budget_preference in ('budget','moderate','premium')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.food_preferences (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references auth.users(id) on delete cascade,
  preference_type text not null check (preference_type in ('favorite','disliked','neutral')),
  food_category text not null,
  food_item text,
  rating int not null check (rating >= 1 and rating <= 5),
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- =========
-- Billing + subscription
-- =========
create table if not exists public.user_saved_cards (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  card_holder_name text,
  card_brand text,
  card_last4 text not null,
  expiry_month int,
  expiry_year int,
  billing_zip text,
  is_default boolean not null default false,
  stripe_payment_method_id text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.user_payment_history (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  stripe_payment_intent_id text,
  stripe_invoice_id text,
  amount_cents int not null,
  currency text not null default 'usd',
  status text,
  plan_name text,
  paid_at timestamptz,
  metadata jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.pricing_plans (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  description text,
  features jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.user_subscriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  plan_name text,
  pricing_plan_id uuid references public.pricing_plans(id),
  status text not null default 'active',
  stripe_subscription_id text,
  current_period_start timestamptz,
  current_period_end timestamptz,
  billing_cycle text default 'monthly' check (billing_cycle in ('monthly','yearly')),
  cancel_at_period_end boolean not null default false,
  auto_renew boolean not null default true,
  next_billing_at timestamptz,
  last_payment_at timestamptz,
  metadata jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(user_id)
);

create table if not exists public.referrals (
  id uuid primary key default gen_random_uuid(),
  referrer_id uuid not null references auth.users(id) on delete cascade,
  referee_id uuid references auth.users(id) on delete set null,
  referral_code text not null,
  status text not null default 'pending',
  created_at timestamptz not null default now()
);

-- =========
-- Trigger helpers
-- =========

do $$
begin
  if not exists (select 1 from pg_trigger where tgname = 'trg_users_updated_at') then
    create trigger trg_users_updated_at before update on public.users for each row execute procedure public.set_updated_at_timestamp();
  end if;
  if not exists (select 1 from pg_trigger where tgname = 'trg_user_profile_details_updated_at') then
    create trigger trg_user_profile_details_updated_at before update on public.user_profile_details for each row execute procedure public.set_updated_at_timestamp();
  end if;
  if not exists (select 1 from pg_trigger where tgname = 'trg_user_addresses_updated_at') then
    create trigger trg_user_addresses_updated_at before update on public.user_addresses for each row execute procedure public.set_updated_at_timestamp();
  end if;
  if not exists (select 1 from pg_trigger where tgname = 'trg_user_profile_preferences_updated_at') then
    create trigger trg_user_profile_preferences_updated_at before update on public.user_profile_preferences for each row execute procedure public.set_updated_at_timestamp();
  end if;
  if not exists (select 1 from pg_trigger where tgname = 'trg_user_discovery_preferences_updated_at') then
    create trigger trg_user_discovery_preferences_updated_at before update on public.user_discovery_preferences for each row execute procedure public.set_updated_at_timestamp();
  end if;
  if not exists (select 1 from pg_trigger where tgname = 'trg_user_health_preferences_updated_at') then
    create trigger trg_user_health_preferences_updated_at before update on public.user_health_preferences for each row execute procedure public.set_updated_at_timestamp();
  end if;
  if not exists (select 1 from pg_trigger where tgname = 'trg_health_profiles_updated_at') then
    create trigger trg_health_profiles_updated_at before update on public.health_profiles for each row execute procedure public.set_updated_at_timestamp();
  end if;
  if not exists (select 1 from pg_trigger where tgname = 'trg_health_conditions_v2_updated_at') then
    create trigger trg_health_conditions_v2_updated_at before update on public.health_conditions_v2 for each row execute procedure public.set_updated_at_timestamp();
  end if;
  if not exists (select 1 from pg_trigger where tgname = 'trg_user_scan_preferences_updated_at') then
    create trigger trg_user_scan_preferences_updated_at before update on public.user_scan_preferences for each row execute procedure public.set_updated_at_timestamp();
  end if;
  if not exists (select 1 from pg_trigger where tgname = 'trg_user_preferences_updated_at') then
    create trigger trg_user_preferences_updated_at before update on public.user_preferences for each row execute procedure public.set_updated_at_timestamp();
  end if;
  if not exists (select 1 from pg_trigger where tgname = 'trg_food_preferences_updated_at') then
    create trigger trg_food_preferences_updated_at before update on public.food_preferences for each row execute procedure public.set_updated_at_timestamp();
  end if;
  if not exists (select 1 from pg_trigger where tgname = 'trg_user_saved_cards_updated_at') then
    create trigger trg_user_saved_cards_updated_at before update on public.user_saved_cards for each row execute procedure public.set_updated_at_timestamp();
  end if;
  if not exists (select 1 from pg_trigger where tgname = 'trg_pricing_plans_updated_at') then
    create trigger trg_pricing_plans_updated_at before update on public.pricing_plans for each row execute procedure public.set_updated_at_timestamp();
  end if;
  if not exists (select 1 from pg_trigger where tgname = 'trg_user_subscriptions_updated_at') then
    create trigger trg_user_subscriptions_updated_at before update on public.user_subscriptions for each row execute procedure public.set_updated_at_timestamp();
  end if;
end $$;

-- =========
-- RLS
-- =========
alter table public.users enable row level security;
alter table public.user_profile_details enable row level security;
alter table public.user_addresses enable row level security;
alter table public.user_profile_preferences enable row level security;
alter table public.user_discovery_preferences enable row level security;
alter table public.user_health_preferences enable row level security;
alter table public.health_conditions enable row level security;
alter table public.health_profiles enable row level security;
alter table public.health_conditions_v2 enable row level security;
alter table public.health_recommendations_cache enable row level security;
alter table public.health_analytics enable row level security;
alter table public.ocr_results enable row level security;
alter table public.user_recent_scans enable row level security;
alter table public.user_scan_preferences enable row level security;
alter table public.user_preferences enable row level security;
alter table public.food_preferences enable row level security;
alter table public.user_saved_cards enable row level security;
alter table public.user_payment_history enable row level security;
alter table public.user_subscriptions enable row level security;
alter table public.referrals enable row level security;

-- Minimal idempotent policies using auth.uid() = user_id style
-- (Skip if already exists.)
do $$
begin
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='user_profile_details' and policyname='upd_profile_details_own') then
    create policy upd_profile_details_own on public.user_profile_details for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='user_discovery_preferences' and policyname='upd_discovery_own') then
    create policy upd_discovery_own on public.user_discovery_preferences for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='user_preferences' and policyname='upd_user_preferences_own') then
    create policy upd_user_preferences_own on public.user_preferences for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='health_conditions' and policyname='upd_health_conditions_own') then
    create policy upd_health_conditions_own on public.health_conditions for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='food_preferences' and policyname='upd_food_preferences_own') then
    create policy upd_food_preferences_own on public.food_preferences for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='user_recent_scans' and policyname='upd_recent_scans_own') then
    create policy upd_recent_scans_own on public.user_recent_scans for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='ocr_results' and policyname='upd_ocr_results_own') then
    create policy upd_ocr_results_own on public.ocr_results for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='user_saved_cards' and policyname='upd_saved_cards_own') then
    create policy upd_saved_cards_own on public.user_saved_cards for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='user_payment_history' and policyname='upd_payment_history_own') then
    create policy upd_payment_history_own on public.user_payment_history for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='user_subscriptions' and policyname='upd_subscriptions_own') then
    create policy upd_subscriptions_own on public.user_subscriptions for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
  end if;
end $$;
