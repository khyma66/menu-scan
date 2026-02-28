-- Supabase schema for all app tabs (Discover, Health, Scan, Profile)
-- Apply in Supabase SQL editor (idempotent and safe to re-run)

create extension if not exists "pgcrypto";

create or replace function public.set_updated_at_timestamp()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- =========================
-- PROFILE TAB
-- =========================
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

alter table public.user_profile_details add column if not exists phone text;
alter table public.user_profile_details add column if not exists avatar_url text;
alter table public.user_profile_details add column if not exists preferred_language text;
alter table public.user_profile_details add column if not exists timezone text;

create table if not exists public.user_profile_preferences (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  notifications_enabled boolean not null default true,
  notification_push_enabled boolean not null default true,
  notification_email_enabled boolean not null default true,
  privacy_profile_visibility text not null default 'private' check (privacy_profile_visibility in ('public', 'friends', 'private')),
  analytics_opt_in boolean not null default true,
  marketing_opt_in boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(user_id)
);

-- =========================
-- HEALTH TAB
-- =========================
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

-- =========================
-- SCAN TAB
-- =========================
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
  processing_status text default 'completed' check (processing_status in ('queued', 'processing', 'completed', 'failed')),
  processing_time_ms int,
  pipeline text,
  ocr_result_id uuid,
  created_at timestamptz not null default now()
);

alter table public.user_recent_scans add column if not exists image_url text;
alter table public.user_recent_scans add column if not exists output_language text;
alter table public.user_recent_scans add column if not exists processing_status text default 'completed';
alter table public.user_recent_scans add column if not exists processing_time_ms int;
alter table public.user_recent_scans add column if not exists ocr_result_id uuid;
alter table public.user_recent_scans add column if not exists created_at timestamptz not null default now();

create table if not exists public.user_scan_preferences (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  default_source text not null default 'camera' check (default_source in ('camera', 'gallery')),
  auto_translate boolean not null default false,
  translate_language text,
  save_scan_history boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(user_id)
);

-- =========================
-- PAYMENT TAB
-- =========================
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

alter table public.user_saved_cards add column if not exists billing_zip text;
alter table public.user_saved_cards add column if not exists is_default boolean not null default false;
alter table public.user_saved_cards add column if not exists updated_at timestamptz not null default now();

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

alter table public.user_payment_history add column if not exists stripe_invoice_id text;
alter table public.user_payment_history add column if not exists paid_at timestamptz;
alter table public.user_payment_history add column if not exists metadata jsonb;

-- =========================
-- SUBSCRIPTION TAB
-- =========================
create table if not exists public.user_subscriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  plan_name text,
  status text not null default 'active',
  stripe_subscription_id text,
  current_period_start timestamptz,
  current_period_end timestamptz,
  billing_cycle text default 'monthly' check (billing_cycle in ('monthly', 'yearly')),
  cancel_at_period_end boolean not null default false,
  auto_renew boolean not null default true,
  next_billing_at timestamptz,
  last_payment_at timestamptz,
  metadata jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.user_subscriptions add column if not exists plan_name text;
alter table public.user_subscriptions add column if not exists billing_cycle text default 'monthly';
alter table public.user_subscriptions add column if not exists cancel_at_period_end boolean not null default false;
alter table public.user_subscriptions add column if not exists auto_renew boolean not null default true;
alter table public.user_subscriptions add column if not exists next_billing_at timestamptz;
alter table public.user_subscriptions add column if not exists last_payment_at timestamptz;
alter table public.user_subscriptions add column if not exists metadata jsonb;

-- =========================
-- DISCOVER TAB
-- =========================
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

-- Indexes
create index if not exists idx_user_profile_details_user_id on public.user_profile_details(user_id);
create index if not exists idx_user_profile_preferences_user_id on public.user_profile_preferences(user_id);
create index if not exists idx_user_health_preferences_user_id on public.user_health_preferences(user_id);
create index if not exists idx_user_recent_scans_user_id on public.user_recent_scans(user_id);
create index if not exists idx_user_recent_scans_scanned_at on public.user_recent_scans(scanned_at desc);
create index if not exists idx_user_scan_preferences_user_id on public.user_scan_preferences(user_id);
create index if not exists idx_user_saved_cards_user_id on public.user_saved_cards(user_id);
create index if not exists idx_user_payment_history_user_id on public.user_payment_history(user_id);
create index if not exists idx_user_subscriptions_user_id on public.user_subscriptions(user_id);
create index if not exists idx_user_discovery_preferences_user_id on public.user_discovery_preferences(user_id);

-- Triggers for updated_at
drop trigger if exists trg_user_profile_details_updated_at on public.user_profile_details;
create trigger trg_user_profile_details_updated_at
before update on public.user_profile_details
for each row execute procedure public.set_updated_at_timestamp();

drop trigger if exists trg_user_profile_preferences_updated_at on public.user_profile_preferences;
create trigger trg_user_profile_preferences_updated_at
before update on public.user_profile_preferences
for each row execute procedure public.set_updated_at_timestamp();

drop trigger if exists trg_user_health_preferences_updated_at on public.user_health_preferences;
create trigger trg_user_health_preferences_updated_at
before update on public.user_health_preferences
for each row execute procedure public.set_updated_at_timestamp();

drop trigger if exists trg_user_scan_preferences_updated_at on public.user_scan_preferences;
create trigger trg_user_scan_preferences_updated_at
before update on public.user_scan_preferences
for each row execute procedure public.set_updated_at_timestamp();

drop trigger if exists trg_user_saved_cards_updated_at on public.user_saved_cards;
create trigger trg_user_saved_cards_updated_at
before update on public.user_saved_cards
for each row execute procedure public.set_updated_at_timestamp();

drop trigger if exists trg_user_subscriptions_updated_at on public.user_subscriptions;
create trigger trg_user_subscriptions_updated_at
before update on public.user_subscriptions
for each row execute procedure public.set_updated_at_timestamp();

drop trigger if exists trg_user_discovery_preferences_updated_at on public.user_discovery_preferences;
create trigger trg_user_discovery_preferences_updated_at
before update on public.user_discovery_preferences
for each row execute procedure public.set_updated_at_timestamp();

-- RLS
alter table public.user_profile_details enable row level security;
alter table public.user_profile_preferences enable row level security;
alter table public.user_health_preferences enable row level security;
alter table public.user_recent_scans enable row level security;
alter table public.user_scan_preferences enable row level security;
alter table public.user_saved_cards enable row level security;
alter table public.user_payment_history enable row level security;
alter table public.user_subscriptions enable row level security;
alter table public.user_discovery_preferences enable row level security;

drop policy if exists "user_profile_details_owner_all" on public.user_profile_details;
create policy "user_profile_details_owner_all"
on public.user_profile_details
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "user_profile_preferences_owner_all" on public.user_profile_preferences;
create policy "user_profile_preferences_owner_all"
on public.user_profile_preferences
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "user_health_preferences_owner_all" on public.user_health_preferences;
create policy "user_health_preferences_owner_all"
on public.user_health_preferences
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "user_recent_scans_owner_all" on public.user_recent_scans;
create policy "user_recent_scans_owner_all"
on public.user_recent_scans
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "user_scan_preferences_owner_all" on public.user_scan_preferences;
create policy "user_scan_preferences_owner_all"
on public.user_scan_preferences
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "user_saved_cards_owner_all" on public.user_saved_cards;
create policy "user_saved_cards_owner_all"
on public.user_saved_cards
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "user_payment_history_owner_all" on public.user_payment_history;
create policy "user_payment_history_owner_all"
on public.user_payment_history
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "user_subscriptions_owner_all" on public.user_subscriptions;
create policy "user_subscriptions_owner_all"
on public.user_subscriptions
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "user_discovery_preferences_owner_all" on public.user_discovery_preferences;
create policy "user_discovery_preferences_owner_all"
on public.user_discovery_preferences
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

-- Grants
grant select, insert, update, delete on public.user_profile_details to authenticated;
grant select, insert, update, delete on public.user_profile_preferences to authenticated;
grant select, insert, update, delete on public.user_health_preferences to authenticated;
grant select, insert, update, delete on public.user_recent_scans to authenticated;
grant select, insert, update, delete on public.user_scan_preferences to authenticated;
grant select, insert, update, delete on public.user_saved_cards to authenticated;
grant select, insert, update, delete on public.user_payment_history to authenticated;
grant select, insert, update, delete on public.user_subscriptions to authenticated;
grant select, insert, update, delete on public.user_discovery_preferences to authenticated;
