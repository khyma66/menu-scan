# Storage Bucket Setup

## ⚠️ Bucket Not Found

The `video-transcripts` bucket needs to be created manually in Supabase Dashboard.

## Quick Setup Steps

### Option 1: Via Supabase Dashboard (Recommended)

1. **Go to Supabase Dashboard**
   - URL: https://supabase.com/dashboard/project/jlfqzcaospvspmzbvbxd/storage/buckets

2. **Create New Bucket**
   - Click **"New bucket"** button
   - Name: `video-transcripts`
   - **Public**: ✅ Yes (required for free tier)
   - File size limit: 50 MB (or leave default)
   - Click **"Create bucket"**

3. **Verify Bucket Created**
   - You should see `video-transcripts` in the buckets list
   - Status should show as "Public"

### Option 2: Via SQL (Requires Service Role Key)

If you have service role key access, run this SQL:

```sql
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'video-transcripts',
    'video-transcripts',
    true,
    52428800,  -- 50MB
    ARRAY['text/plain']
)
ON CONFLICT (id) DO NOTHING;
```

## After Creating Bucket

Once the bucket is created, run:

```bash
cd video-transcript-pipeline
source venv/bin/activate
python3 run_with_bucket_check.py
```

Or use the original script:

```bash
python3 process_srichagant_channel.py
```

## Verify Bucket

Check if bucket exists:

```bash
python3 create_bucket.py
```

## Storage Policies

The bucket needs these policies (already set up via `setup_playlist_tables.sql`):

- ✅ Public read access
- ✅ Authenticated upload
- ✅ Authenticated update
- ✅ Authenticated delete

## Next Steps

1. ✅ Create bucket in dashboard
2. ✅ Verify bucket is public
3. ✅ Run pipeline script
4. ✅ Monitor storage usage (stops at 1GB)

