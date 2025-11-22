-- Fix RLS policies for telugu_transcripts table
-- Run this in Supabase SQL Editor

-- First, disable RLS temporarily
ALTER TABLE telugu_transcripts DISABLE ROW LEVEL SECURITY;

-- Drop all existing policies
DROP POLICY IF EXISTS "Allow public read access" ON telugu_transcripts;
DROP POLICY IF EXISTS "Allow authenticated insert" ON telugu_transcripts;
DROP POLICY IF EXISTS "Allow authenticated update" ON telugu_transcripts;
DROP POLICY IF EXISTS "Allow all operations telugu" ON telugu_transcripts;

-- Re-enable RLS
ALTER TABLE telugu_transcripts ENABLE ROW LEVEL SECURITY;

-- Create permissive policies that allow all operations
CREATE POLICY "Allow all SELECT" ON telugu_transcripts
    FOR SELECT USING (true);

CREATE POLICY "Allow all INSERT" ON telugu_transcripts
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow all UPDATE" ON telugu_transcripts
    FOR UPDATE USING (true) WITH CHECK (true);

CREATE POLICY "Allow all DELETE" ON telugu_transcripts
    FOR DELETE USING (true);

-- Verify policies
SELECT schemaname, tablename, policyname, cmd 
FROM pg_policies 
WHERE tablename = 'telugu_transcripts';

