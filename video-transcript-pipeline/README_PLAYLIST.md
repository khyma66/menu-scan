# Playlist Transcript Pipeline - Quick Guide

## Overview

This pipeline processes YouTube channel playlists, extracts transcripts from each video using NoteGPT, and stores them in separate Supabase tables organized by playlist.

## Database Tables

### 1. `playlists` Table
Stores playlist metadata:
- `playlist_id`: YouTube playlist ID
- `title`: Playlist title
- `url`: Playlist URL
- `video_count`: Total videos in playlist
- `processed_videos`: Successfully processed count
- `failed_videos`: Failed count
- `status`: Processing status

### 2. `playlist_transcripts` Table
Stores individual video transcripts with playlist context:
- `playlist_id`: Links to playlists table
- `playlist_title`: Playlist name
- `video_id`: YouTube video ID
- `youtube_url`: Full video URL
- `title`: Video title
- `transcript`: First 5000 chars (full transcript in storage)
- `storage_path`: Path to full transcript file
- `storage_url`: Public URL to transcript
- `metadata`: JSONB with additional data

## Setup

### 1. Create Database Tables

Run `setup_playlist_tables.sql` in Supabase SQL Editor:

```bash
# Copy contents of setup_playlist_tables.sql
# Paste in Supabase SQL Editor
# Execute
```

### 2. Configure Environment

Ensure `.env` has:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
```

### 3. Process Specific Channel

For channel `srichagantikoteswararaogar4451`:

```bash
cd video-transcript-pipeline
python process_srichagant_channel.py
```

Or use the generic pipeline:

```bash
python playlist_pipeline.py
```

## Usage

### Process All Playlists from Channel

```python
from playlist_pipeline import PlaylistTranscriptPipeline

pipeline = PlaylistTranscriptPipeline(
    supabase_url="https://your-project.supabase.co",
    supabase_key="your-key"
)

results = await pipeline.process_channel_playlists(
    channel_url="https://www.youtube.com/@srichagantikoteswararaogar4451",
    max_playlists=None,  # All playlists
    max_videos_per_playlist=None,  # All videos
    delay_between_videos=3.0
)
```

### Process Specific Playlist

```python
from youtube_playlist_extractor import YouTubePlaylistExtractor

extractor = YouTubePlaylistExtractor()
videos = extractor.get_playlist_videos(
    "https://www.youtube.com/playlist?list=PLAYLIST_ID"
)
```

## Storage Structure

Transcripts are stored in Supabase storage with this structure:

```
video-transcripts/
└── playlists/
    └── {playlist_id}/
        └── {video_id}_{sanitized_title}.txt
```

## Querying Results

### Get All Playlists

```sql
SELECT * FROM playlists ORDER BY created_at DESC;
```

### Get Transcripts for a Playlist

```sql
SELECT * FROM playlist_transcripts 
WHERE playlist_id = 'PLAYLIST_ID' 
ORDER BY created_at DESC;
```

### Get All Transcripts with Playlist Info

```sql
SELECT 
    pt.*,
    p.title as playlist_title,
    p.video_count as playlist_video_count
FROM playlist_transcripts pt
JOIN playlists p ON pt.playlist_id = p.playlist_id
ORDER BY pt.created_at DESC;
```

## Features

- ✅ Separate tables for playlists and transcripts
- ✅ Playlist-level organization
- ✅ Full transcript in storage, metadata in database
- ✅ Error handling and retry logic
- ✅ Progress tracking per playlist
- ✅ Free tier optimized

## Notes

- Full transcripts stored in storage bucket
- First 5000 chars stored in database for quick access
- Each playlist gets its own folder in storage
- Unique constraint on (playlist_id, video_id)

