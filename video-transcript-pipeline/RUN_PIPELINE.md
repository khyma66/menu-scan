# Pipeline Deployment Status

## ✅ Supabase Tables Deployed

The following tables have been successfully created in Supabase:

1. **`playlists`** - Stores playlist metadata
   - Columns: id, playlist_id, title, url, video_count, processed_videos, failed_videos, status, created_at, updated_at
   - RLS enabled with public read access

2. **`playlist_transcripts`** - Stores video transcripts with playlist context
   - Columns: id, playlist_id, playlist_title, video_id, youtube_url, title, transcript, storage_path, storage_url, metadata, created_at, updated_at
   - Unique constraint on (playlist_id, video_id)
   - RLS enabled with public read access

## 🚀 Pipeline Running

The pipeline is now running in the background to process:
- **Channel**: `@srichagantikoteswararaogar4451`
- **Process**: Extracting playlists → Extracting videos → Getting transcripts → Storing in Supabase

## 📊 Monitor Progress

### Check Playlists Table
```sql
SELECT * FROM playlists ORDER BY created_at DESC;
```

### Check Transcripts Table
```sql
SELECT 
    playlist_title,
    title,
    created_at
FROM playlist_transcripts 
ORDER BY created_at DESC 
LIMIT 10;
```

### Check Processing Status
```sql
SELECT 
    title,
    video_count,
    processed_videos,
    failed_videos,
    status
FROM playlists;
```

## 🔍 Storage Location

Transcripts are stored in Supabase Storage:
- **Bucket**: `video-transcripts`
- **Path**: `playlists/{playlist_id}/{video_id}_{title}.txt`

## ⚙️ Configuration

- **Supabase URL**: `https://jlfqzcaospvspmzbvbxd.supabase.co`
- **Environment**: Virtual environment created at `venv/`
- **Dependencies**: Installed (supabase, yt-dlp, playwright, python-dotenv, mcp)

## 📝 Next Steps

1. Monitor the pipeline progress in Supabase dashboard
2. Check logs if needed
3. Query results using SQL above
4. Access transcripts via storage URLs

## 🛠️ Troubleshooting

If the pipeline stops or encounters errors:
1. Check Supabase logs
2. Verify storage bucket exists and is public
3. Check network connectivity
4. Re-run: `python3 process_srichagant_channel.py`

