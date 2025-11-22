# Supabase Storage Bucket Setup

## Manual Bucket Creation Required

The `video-transcripts` bucket needs to be created manually in the Supabase Dashboard.

### Steps:

1. **Go to Supabase Dashboard**
   - Navigate to: https://supabase.com/dashboard
   - Select your project: `jlfqzcaospvspmzbvbxd`

2. **Create Bucket**
   - Click on **Storage** in the left sidebar
   - Click **Create Bucket** button
   - Fill in:
     - **Name**: `video-transcripts`
     - **Public**: ✅ **Yes** (Required for free tier access)
     - **File size limit**: 100 MB (optional)
   - Click **Create**

3. **Verify**
   - The bucket should appear in the Storage list
   - Status should show as "Public"

### After Creation

Once the bucket is created, the pipeline will automatically:
- Upload SRT subtitle files
- Upload VTT subtitle files  
- Upload full transcript text files
- Store metadata in the `telugu_transcripts` table

### Note

The pipeline will still work without the bucket - it will store transcript data in the database, but file uploads will be skipped until the bucket is created.
