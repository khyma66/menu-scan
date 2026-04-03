-- ============================================================
-- profiles table — synced from auth.users on every login/signup
-- Run this in Supabase SQL Editor (Dashboard > SQL Editor > New query)
-- ============================================================

-- 1. Create the profiles table
create table if not exists public.profiles (
    id          uuid primary key references auth.users(id) on delete cascade,
    full_name   text,
    email       text,
    phone       text,
    country     text,
    avatar_url  text,
    provider    text default 'email',   -- 'google' | 'apple' | 'email'
    created_at  timestamptz default now(),
    updated_at  timestamptz default now()
);

-- 2. Enable Row Level Security
alter table public.profiles enable row level security;

-- 3. RLS Policies — users can only see and edit their own row
drop policy if exists "Users can view own profile"   on public.profiles;
drop policy if exists "Users can insert own profile" on public.profiles;
drop policy if exists "Users can update own profile" on public.profiles;

create policy "Users can view own profile"
    on public.profiles for select
    using (auth.uid() = id);

create policy "Users can insert own profile"
    on public.profiles for insert
    with check (auth.uid() = id);

create policy "Users can update own profile"
    on public.profiles for update
    using (auth.uid() = id);

-- 4. Auto-create / auto-update profile row when a user signs up or logs in via OAuth
--    Reads name + avatar from OAuth metadata automatically.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
    insert into public.profiles (id, full_name, email, avatar_url, provider)
    values (
        new.id,
        coalesce(
            new.raw_user_meta_data->>'full_name',
            new.raw_user_meta_data->>'name'
        ),
        new.email,
        new.raw_user_meta_data->>'avatar_url',
        coalesce(new.raw_app_meta_data->>'provider', 'email')
    )
    on conflict (id) do update
        set full_name  = coalesce(excluded.full_name,  profiles.full_name),
            email      = coalesce(excluded.email,      profiles.email),
            avatar_url = coalesce(excluded.avatar_url, profiles.avatar_url),
            provider   = coalesce(excluded.provider,   profiles.provider),
            updated_at = now();
    return new;
end;
$$;

-- Drop old trigger if it exists, then re-create
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
    after insert on auth.users
    for each row execute procedure public.handle_new_user();

-- 5. updated_at auto-stamp on every update
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists set_profiles_updated_at on public.profiles;
create trigger set_profiles_updated_at
    before update on public.profiles
    for each row execute procedure public.set_updated_at();

-- 6. Back-fill existing users (one-time, safe to re-run)
insert into public.profiles (id, full_name, email, avatar_url, provider)
select
    id,
    coalesce(raw_user_meta_data->>'full_name', raw_user_meta_data->>'name'),
    email,
    raw_user_meta_data->>'avatar_url',
    coalesce(raw_app_meta_data->>'provider', 'email')
from auth.users
on conflict (id) do update
    set full_name  = coalesce(excluded.full_name,  profiles.full_name),
        email      = coalesce(excluded.email,      profiles.email),
        avatar_url = coalesce(excluded.avatar_url, profiles.avatar_url),
        provider   = coalesce(excluded.provider,   profiles.provider),
        updated_at = now();
