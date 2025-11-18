# Quick Deploy Guide

## 🚀 Deploy Pipeline in 3 Steps

### Step 1: Create Storage Bucket

**Go to Supabase Dashboard:**
https://supabase.com/dashboard/project/jlfqzcaospvspmzbvbxd/storage/buckets

1. Click **"New bucket"**
2. Name: `video-transcripts`
3. **Public**: ✅ Yes
4. Click **"Create bucket"**

### Step 2: Verify Setup

```bash
cd video-transcript-pipeline
source venv/bin/activate
python3 run_with_bucket_check.py
```

This will:
- ✅ Check if bucket exists
- ✅ Verify tables are set up
- ✅ Start processing if everything is ready

### Step 3: Run Pipeline

If bucket exists, the script will automatically start processing:

```bash
python3 run_with_bucket_check.py
```

Or use the channel-specific script:

```bash
python3 process_srichagant_channel.py
```

## ✅ What's Already Done

- ✅ Database tables created (`playlists`, `playlist_transcripts`)
- ✅ Storage policies configured
- ✅ Storage limit monitoring (stops at 1GB)
- ✅ Dependencies installed
- ✅ Scripts ready to run

## 📊 Monitor Progress

Check progress in Supabase:

```sql
-- Check playlists
SELECT * FROM playlists ORDER BY created_at DESC;

-- Check transcripts
SELECT COUNT(*) FROM playlist_transcripts;

-- Check storage usage
SELECT 
    COUNT(*) as file_count,
    COUNT(*) * 50 * 1024 as estimated_size_bytes,
    (COUNT(*) * 50 * 1024) / (1024.0 * 1024.0 * 1024.0) as estimated_size_gb
FROM playlist_transcripts;
```

## 🎯 Expected Behavior

- Pipeline processes playlists from channel
- Extracts transcripts via NoteGPT
- Stores in Supabase (database + storage)
- **Stops automatically at 1GB storage limit**
- Saves all progress before stopping

## ⚠️ Troubleshooting

**Bucket not found?**
- Create it manually in dashboard (see Step 1)
- Or check: `python3 create_bucket.py`

**Pipeline stops early?**
- Check storage usage in Supabase dashboard
- Verify 1GB limit hasn't been reached
- Check logs for errors

**Need to restart?**
- Just run the script again
- It will skip already processed videos (unique constraint)

