-- Drop duplicate v2 health tables (health_conditions_v2, health_profiles)
-- Keep: health_conditions (legacy), user_health_preferences (compact arrays)

-- Drop triggers first
drop trigger if exists trg_health_conditions_v2_updated_at on public.health_conditions_v2;
drop trigger if exists trg_health_profiles_updated_at on public.health_profiles;

-- Drop policies
do $$
begin
  -- health_conditions_v2 policies
  begin
    drop policy if exists "upd_health_conditions_v2_own" on public.health_conditions_v2;
  exception when undefined_table then null;
  end;
end $$;

-- Drop tables (cascade to handle FK references)
drop table if exists public.health_conditions_v2 cascade;
drop table if exists public.health_profiles cascade;
