-- ============================================================
-- Subscription schema (commission-free via web / Stripe)
-- Apply in Supabase SQL editor — idempotent / safe to re-run
-- ============================================================

-- ── Plan definitions (source of truth kept in DB so native apps can read them)
create table if not exists public.subscription_plans (
  id            text primary key,                   -- e.g. "free", "pro", "max"
  display_name  text not null,
  description   text,
  price_monthly_cents  int  not null default 0,     -- 0 = free
  price_yearly_cents   int,
  currency      text not null default 'usd',
  stripe_price_monthly text,                        -- Stripe price ID
  stripe_price_yearly  text,
  scan_limit_monthly   int  not null default 3,     -- -1 = unlimited
  features      text[] not null default '{}',
  is_active     boolean not null default true,
  sort_order    int not null default 0
);

insert into public.subscription_plans
  (id, display_name, description, price_monthly_cents, price_yearly_cents,
   stripe_price_monthly, stripe_price_yearly,
   scan_limit_monthly, features, sort_order)
values
  ('free', 'Free',      'Get started for free',
   0, null, null, null, 3,
   array['3 scans / month','Basic nutrition info','Allergen alerts'],
   0),
  ('pro',  'Pro',       'For food-conscious individuals',
   499, 3999, 'price_pro_monthly', 'price_pro_yearly', -1,
   array['Unlimited scans','Full nutrition details','Translation','Ingredient breakdown','Priority processing'],
   1),
  ('max',  'Max',       'Power users & families',
   999, 7999, 'price_max_monthly', 'price_max_yearly', -1,
   array['Everything in Pro','Early access features','Multi-language menus','Dedicated support'],
   2)
on conflict (id) do update set
  display_name         = excluded.display_name,
  price_monthly_cents  = excluded.price_monthly_cents,
  price_yearly_cents   = excluded.price_yearly_cents,
  scan_limit_monthly   = excluded.scan_limit_monthly,
  features             = excluded.features;

-- ── Per-user subscriptions (updated by Stripe webhook only)
create table if not exists public.user_subscriptions (
  id                   uuid primary key default gen_random_uuid(),
  user_id              uuid not null references auth.users(id) on delete cascade,
  plan_id              text not null references public.subscription_plans(id)
                         default 'free',
  status               text not null default 'active'
                         check (status in ('trialing','active','past_due','canceled','paused','incomplete')),
  stripe_customer_id   text,
  stripe_subscription_id text,
  stripe_price_id      text,
  billing_cycle        text check (billing_cycle in ('monthly','yearly')),
  current_period_start timestamptz,
  current_period_end   timestamptz,
  cancel_at_period_end boolean not null default false,
  trial_end            timestamptz,
  -- grace period: remain active for 7 days after payment failure
  grace_period_end     timestamptz,
  -- purchased via web (never via IAP — avoids store commission)
  purchase_channel     text not null default 'web'
                         check (purchase_channel in ('web','promo','gift','legacy')),
  created_at           timestamptz not null default now(),
  updated_at           timestamptz not null default now(),
  unique (user_id)     -- one active subscription per user
);

-- Add columns safely if table already exists
alter table public.user_subscriptions
  add column if not exists grace_period_end timestamptz;
alter table public.user_subscriptions
  add column if not exists trial_end timestamptz;
alter table public.user_subscriptions
  add column if not exists purchase_channel text not null default 'web';

-- ── Webhook event log (idempotency — prevent double-processing)
create table if not exists public.stripe_webhook_events (
  stripe_event_id  text primary key,
  event_type       text not null,
  processed_at     timestamptz not null default now(),
  payload          jsonb
);

-- ── Stripe checkout sessions (track pending → success state)
create table if not exists public.checkout_sessions (
  id               uuid primary key default gen_random_uuid(),
  user_id          uuid not null references auth.users(id) on delete cascade,
  stripe_session_id text unique,
  plan_id          text references public.subscription_plans(id),
  billing_cycle    text,
  status           text not null default 'pending'
                     check (status in ('pending','complete','expired','canceled')),
  -- deep-link to open after success (e.g. menuocr://subscription-result?status=success)
  success_deeplink text,
  cancel_deeplink  text,
  created_at       timestamptz not null default now(),
  expires_at       timestamptz
);

-- ── Auto-updated timestamp
create or replace function public.set_sub_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_user_sub_updated on public.user_subscriptions;
create trigger trg_user_sub_updated
  before update on public.user_subscriptions
  for each row execute function public.set_sub_updated_at();

-- ── Auto-create free subscription on signup
create or replace function public.handle_new_user_subscription()
returns trigger language plpgsql security definer as $$
begin
  insert into public.user_subscriptions (user_id, plan_id, status, purchase_channel)
  values (new.id, 'free', 'active', 'web')
  on conflict (user_id) do nothing;
  return new;
end;
$$;

drop trigger if exists trg_new_user_subscription on auth.users;
create trigger trg_new_user_subscription
  after insert on auth.users
  for each row execute function public.handle_new_user_subscription();

-- Back-fill free tier for existing users without a subscription row
insert into public.user_subscriptions (user_id, plan_id, status, purchase_channel)
  select id, 'free', 'active', 'web' from auth.users
  where id not in (select user_id from public.user_subscriptions)
on conflict (user_id) do nothing;

-- ── RLS
alter table public.user_subscriptions      enable row level security;
alter table public.subscription_plans      enable row level security;
alter table public.checkout_sessions       enable row level security;
alter table public.stripe_webhook_events   enable row level security;

-- Plans are public-readable
drop policy if exists "plans_public_read" on public.subscription_plans;
create policy "plans_public_read" on public.subscription_plans
  for select using (true);

-- Users can only read/update their own subscription
drop policy if exists "sub_own_read"   on public.user_subscriptions;
drop policy if exists "sub_own_update" on public.user_subscriptions;
create policy "sub_own_read" on public.user_subscriptions
  for select using (auth.uid() = user_id);
create policy "sub_own_update" on public.user_subscriptions
  for update using (auth.uid() = user_id);

-- Checkout sessions: own only
drop policy if exists "checkout_own" on public.checkout_sessions;
create policy "checkout_own" on public.checkout_sessions
  for all using (auth.uid() = user_id);

-- Stripe webhook events: service role only (no user policies)
drop policy if exists "webhook_service_only" on public.stripe_webhook_events;
create policy "webhook_service_only" on public.stripe_webhook_events
  for all using (false);   -- only service_role key bypasses RLS

-- Useful view: fast plan check for API + native apps
create or replace view public.user_plan_status as
  select
    u.id                         as user_id,
    u.email,
    coalesce(s.plan_id, 'free')  as plan_id,
    p.display_name               as plan_name,
    coalesce(s.status, 'active') as status,
    p.scan_limit_monthly,
    p.features,
    s.current_period_end,
    s.cancel_at_period_end,
    s.stripe_customer_id,
    -- Is subscription currently effective (active or in grace period)?
    case
      when coalesce(s.status, 'active') = 'active'   then true
      when s.status = 'trialing'                      then true
      when s.status = 'past_due'
        and s.grace_period_end > now()               then true
      else false
    end as is_effective
  from auth.users u
  left join public.user_subscriptions s on s.user_id = u.id
  left join public.subscription_plans p on p.id = coalesce(s.plan_id, 'free');
