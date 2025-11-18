-- Create playlists table for storing playlist metadata
CREATE TABLE IF NOT EXISTS playlists (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    playlist_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    video_count INTEGER DEFAULT 0,
    processed_videos INTEGER DEFAULT 0,
    failed_videos INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create playlist_transcripts table for storing transcripts with playlist context
CREATE TABLE IF NOT EXISTS playlist_transcripts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    playlist_id TEXT NOT NULL,
    playlist_title TEXT NOT NULL,
    video_id TEXT NOT NULL,
    youtube_url TEXT NOT NULL,
    title TEXT NOT NULL,
    transcript TEXT, -- First 5000 chars stored in DB, full transcript in storage
    storage_path TEXT NOT NULL,
    storage_url TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(playlist_id, video_id)
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_playlists_playlist_id ON playlists(playlist_id);
CREATE INDEX IF NOT EXISTS idx_playlists_created_at ON playlists(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_playlist_transcripts_playlist_id ON playlist_transcripts(playlist_id);
CREATE INDEX IF NOT EXISTS idx_playlist_transcripts_video_id ON playlist_transcripts(video_id);
CREATE INDEX IF NOT EXISTS idx_playlist_transcripts_created_at ON playlist_transcripts(created_at DESC);

-- Enable Row Level Security (RLS) - free tier compatible
ALTER TABLE playlists ENABLE ROW LEVEL SECURITY;
ALTER TABLE playlist_transcripts ENABLE ROW LEVEL SECURITY;

-- Create policy to allow public read access
CREATE POLICY "Allow public read access playlists" ON playlists
    FOR SELECT
    USING (true);

CREATE POLICY "Allow public read access playlist_transcripts" ON playlist_transcripts
    FOR SELECT
    USING (true);

-- Create policy to allow authenticated insert
CREATE POLICY "Allow authenticated insert playlists" ON playlists
    FOR INSERT
    WITH CHECK (true);

CREATE POLICY "Allow authenticated insert playlist_transcripts" ON playlist_transcripts
    FOR INSERT
    WITH CHECK (true);

-- Create policy to allow authenticated update
CREATE POLICY "Allow authenticated update playlists" ON playlists
    FOR UPDATE
    USING (true);

CREATE POLICY "Allow authenticated update playlist_transcripts" ON playlist_transcripts
    FOR UPDATE
    USING (true);

