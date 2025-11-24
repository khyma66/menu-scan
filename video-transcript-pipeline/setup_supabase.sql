-- Create video_transcripts table for storing transcript metadata
-- This uses Supabase free tier features

CREATE TABLE IF NOT EXISTS video_transcripts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    video_id TEXT NOT NULL UNIQUE,
    youtube_url TEXT NOT NULL,
    title TEXT NOT NULL,
    transcript TEXT, -- First 5000 chars stored in DB, full transcript in storage
    storage_path TEXT NOT NULL,
    storage_url TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_video_transcripts_video_id ON video_transcripts(video_id);
CREATE INDEX IF NOT EXISTS idx_video_transcripts_created_at ON video_transcripts(created_at DESC);

-- Enable Row Level Security (RLS) - free tier compatible
ALTER TABLE video_transcripts ENABLE ROW LEVEL SECURITY;

-- Create policy to allow public read access (adjust based on your needs)
CREATE POLICY "Allow public read access" ON video_transcripts
    FOR SELECT
    USING (true);

-- Create policy to allow authenticated insert (adjust based on your needs)
CREATE POLICY "Allow authenticated insert" ON video_transcripts
    FOR INSERT
    WITH CHECK (true);

-- Create storage bucket (run this in Supabase SQL editor)
-- Note: For free tier, you may need to create the bucket manually in the dashboard
-- INSERT INTO storage.buckets (id, name, public) VALUES ('video-transcripts', 'video-transcripts', true);

-- Create storage policy for public read access
CREATE POLICY "Public read access" ON storage.objects
    FOR SELECT
    USING (bucket_id = 'video-transcripts');

-- Create storage policy for authenticated upload
CREATE POLICY "Authenticated upload" ON storage.objects
    FOR INSERT
    WITH CHECK (bucket_id = 'video-transcripts');

-- Create storage policy for authenticated update
CREATE POLICY "Authenticated update" ON storage.objects
    FOR UPDATE
    USING (bucket_id = 'video-transcripts');

-- Create storage policy for authenticated delete
CREATE POLICY "Authenticated delete" ON storage.objects
    FOR DELETE
    USING (bucket_id = 'video-transcripts');

