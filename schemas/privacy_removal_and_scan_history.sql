-- ============================================================
-- Migration: Privacy Tab Removal & Scan History Enhancement
-- Date: 2026-03-11
-- Description:
--   1. Privacy fields (privacy_profile_visibility, analytics_opt_in,
--      marketing_opt_in) are kept with defaults for backward compat
--      but are no longer exposed in the UI.
--   2. Ensure user_recent_scans table, indexes, and RLS are correct
--      for the new per-account daily scan history feature.
-- ============================================================

-- ──────────────────────────────────────────────────
-- 1. Set default values for privacy columns (no-op if already correct)
--    These columns stay in the schema but are no longer user-facing.
-- ──────────────────────────────────────────────────
ALTER TABLE public.user_profile_preferences
  ALTER COLUMN privacy_profile_visibility SET DEFAULT 'private';

ALTER TABLE public.user_profile_preferences
  ALTER COLUMN analytics_opt_in SET DEFAULT true;

ALTER TABLE public.user_profile_preferences
  ALTER COLUMN marketing_opt_in SET DEFAULT false;

-- Add a comment explaining deprecation
COMMENT ON COLUMN public.user_profile_preferences.privacy_profile_visibility IS
  'Deprecated: Privacy tab removed from UI (2026-03-11). Kept for backward compat with default value.';
COMMENT ON COLUMN public.user_profile_preferences.analytics_opt_in IS
  'Deprecated: Privacy tab removed from UI (2026-03-11). Defaults to true.';
COMMENT ON COLUMN public.user_profile_preferences.marketing_opt_in IS
  'Deprecated: Privacy tab removed from UI (2026-03-11). Defaults to false.';

-- ──────────────────────────────────────────────────
-- 2. Ensure user_recent_scans table exists with all required columns
-- ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.user_recent_scans (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  scanned_at timestamptz NOT NULL DEFAULT now(),
  source text,
  image_name text,
  image_url text,
  detected_language text,
  output_language text,
  dish_count int,
  processing_status text DEFAULT 'completed'
    CHECK (processing_status IN ('queued','processing','completed','failed')),
  processing_time_ms int,
  pipeline text,
  ocr_result_id uuid,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Ensure all columns exist (idempotent ALTER for columns added later)
ALTER TABLE public.user_recent_scans ADD COLUMN IF NOT EXISTS image_url text;
ALTER TABLE public.user_recent_scans ADD COLUMN IF NOT EXISTS output_language text;
ALTER TABLE public.user_recent_scans ADD COLUMN IF NOT EXISTS processing_status text DEFAULT 'completed';
ALTER TABLE public.user_recent_scans ADD COLUMN IF NOT EXISTS processing_time_ms int;
ALTER TABLE public.user_recent_scans ADD COLUMN IF NOT EXISTS ocr_result_id uuid;
ALTER TABLE public.user_recent_scans ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now();

-- ──────────────────────────────────────────────────
-- 3. Indexes for efficient per-user daily scan queries
-- ──────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_user_recent_scans_user_id
  ON public.user_recent_scans(user_id);

CREATE INDEX IF NOT EXISTS idx_user_recent_scans_scanned_at
  ON public.user_recent_scans(scanned_at DESC);

-- Composite index for user + date range queries (most common query pattern)
CREATE INDEX IF NOT EXISTS idx_user_recent_scans_user_scanned_desc
  ON public.user_recent_scans(user_id, scanned_at DESC);

-- ──────────────────────────────────────────────────
-- 4. Row Level Security
-- ──────────────────────────────────────────────────
ALTER TABLE public.user_recent_scans ENABLE ROW LEVEL SECURITY;

-- Users can only see/modify their own scans
DROP POLICY IF EXISTS "user_recent_scans_owner_all" ON public.user_recent_scans;
CREATE POLICY "user_recent_scans_owner_all"
  ON public.user_recent_scans
  FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- ──────────────────────────────────────────────────
-- 5. Verify
-- ──────────────────────────────────────────────────
DO $$
BEGIN
  RAISE NOTICE '✅ Privacy fields deprecated (defaults kept)';
  RAISE NOTICE '✅ user_recent_scans table ready with indexes and RLS';
END $$;
