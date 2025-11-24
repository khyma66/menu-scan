# Pipeline Status & Process Flow

## ✅ Current Process Flow

### Step-by-Step Process:

1. **Extract Playlists** → Get all playlists from YouTube channel
2. **Extract Video URLs** → Get all video URLs from each playlist
3. **For Each Video URL**:
   - Pass URL to NoteGPT.io website
   - Extract transcript from NoteGPT
   - Store transcript in `playlist_transcripts` table (separate row per video)
   - Store full transcript in storage bucket

## 📊 Table Structure

### `playlist_transcripts` Table
Each video transcript is stored as a **separate row**:

```sql
CREATE TABLE playlist_transcripts (
    id UUID PRIMARY KEY,
    playlist_id TEXT,           -- Links to playlist
    playlist_title TEXT,        -- Playlist name
    video_id TEXT,              -- YouTube video ID
    youtube_url TEXT,           -- Full YouTube URL
    title TEXT,                 -- Video title
    transcript TEXT,            -- First 5000 chars in DB
    storage_path TEXT,          -- Path to full transcript file
    storage_url TEXT,           -- Public URL to transcript
    metadata JSONB,             -- Additional metadata
    created_at TIMESTAMPTZ,     -- When stored
    UNIQUE(playlist_id, video_id) -- One row per video
);
```

## 🔄 Current Pipeline Status

**Pipeline Running**: ✅ Background process active

**Process**:
- ✅ Extracting playlists
- ✅ Extracting video URLs  
- ✅ Processing each URL through NoteGPT
- ✅ Storing in separate table rows

## 📝 How It Works

### For Each Video URL:

```python
1. Get YouTube URL: https://www.youtube.com/watch?v=VIDEO_ID
2. Pass to NoteGPT.io: Paste URL in website
3. Extract transcript: Get text from NoteGPT
4. Store in database: INSERT INTO playlist_transcripts
   - Each video = One row
   - Separate row for each transcript
5. Store full transcript: Upload to storage bucket
```

## ✅ Verification

Check if transcripts are being stored:

```sql
-- Count transcripts stored
SELECT COUNT(*) FROM playlist_transcripts;

-- View recent transcripts
SELECT 
    playlist_title,
    title,
    LENGTH(transcript) as transcript_length,
    created_at
FROM playlist_transcripts
ORDER BY created_at DESC
LIMIT 10;

-- Check by playlist
SELECT 
    playlist_title,
    COUNT(*) as video_count
FROM playlist_transcripts
GROUP BY playlist_title;
```

## 🎯 Expected Results

- Each video URL → One transcript → One database row
- All transcripts stored in `playlist_transcripts` table
- Full transcripts in storage bucket
- Metadata linked to playlists

## 📊 Monitor Progress

```sql
-- Real-time progress
SELECT 
    (SELECT COUNT(*) FROM playlists) as playlists_found,
    (SELECT COUNT(*) FROM playlist_transcripts) as transcripts_stored,
    (SELECT COUNT(DISTINCT video_id) FROM playlist_transcripts) as unique_videos;
```

