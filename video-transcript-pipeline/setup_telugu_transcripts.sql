-- Create telugu_transcripts table for storing Telugu video transcripts
-- Uses Whisper ASR + LLM enhancement

CREATE TABLE IF NOT EXISTS telugu_transcripts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    video_id TEXT NOT NULL UNIQUE,
    youtube_url TEXT NOT NULL,
    title TEXT NOT NULL,
    playlist_id TEXT,
    playlist_title TEXT,
    
    -- Transcripts
    raw_transcript TEXT,  -- Raw output from Whisper ASR
    enhanced_transcript TEXT,  -- LLM-enhanced transcript (first 10K chars)
    
    -- Storage paths
    full_transcript_storage_path TEXT NOT NULL,
    srt_storage_path TEXT NOT NULL,
    vtt_storage_path TEXT NOT NULL,
    
    -- Public URLs
    srt_url TEXT NOT NULL,
    vtt_url TEXT NOT NULL,
    
    -- Metadata
    segments_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_telugu_transcripts_video_id ON telugu_transcripts(video_id);
CREATE INDEX IF NOT EXISTS idx_telugu_transcripts_playlist_id ON telugu_transcripts(playlist_id);
CREATE INDEX IF NOT EXISTS idx_telugu_transcripts_created_at ON telugu_transcripts(created_at DESC);

-- Enable RLS
ALTER TABLE telugu_transcripts ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY IF NOT EXISTS "Allow public read access" ON telugu_transcripts
    FOR SELECT USING (true);

CREATE POLICY IF NOT EXISTS "Allow authenticated insert" ON telugu_transcripts
    FOR INSERT WITH CHECK (true);

CREATE POLICY IF NOT EXISTS "Allow authenticated update" ON telugu_transcripts
    FOR UPDATE USING (true);

