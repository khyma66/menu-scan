# Storage Limit Monitoring

## Overview

The pipeline now includes automatic storage monitoring to prevent exceeding the Supabase free tier limit of **1GB**.

## Features

### ✅ Automatic Storage Monitoring
- Checks storage usage before processing each video
- Estimates storage based on file count (average 50KB per transcript)
- Warns at 90% usage
- Stops automatically at 100% usage

### ✅ Graceful Shutdown
- Pipeline stops gracefully when storage limit is reached
- Current progress is saved
- Clear error messages indicating why pipeline stopped

## How It Works

1. **Before Processing Each Video**:
   - Estimates transcript size (~50KB)
   - Checks if adding it would exceed 1GB limit
   - Shows warning if approaching 90% usage

2. **After Extracting Transcript**:
   - Checks actual transcript size
   - Verifies storage limit won't be exceeded
   - Skips video if limit would be exceeded

3. **When Limit Reached**:
   - Stops processing current playlist
   - Saves all progress to database
   - Returns summary with storage information

## Configuration

Default storage limit is set to **1.0 GB** (free tier limit):

```python
pipeline = PlaylistTranscriptPipeline(
    supabase_url=supabase_url,
    supabase_key=supabase_key,
    bucket_name="video-transcripts",
    storage_limit_gb=1.0  # Free tier limit
)
```

You can adjust this if you have a higher tier:

```python
storage_limit_gb=5.0  # For 5GB limit
```

## Monitoring Output

The pipeline will show:

```
⚠️  Storage warning: 85.2% used
   Current: 0.85 GB / Limit: 1.00 GB
```

When limit is reached:

```
⚠️  STORAGE LIMIT EXCEEDED!
Current usage: 1.02 GB
Limit: 1.00 GB
Usage: 102.0%
============================================================
Stopping pipeline to prevent exceeding storage limit.
```

## Storage Estimation

Since Supabase doesn't provide direct storage usage API, the pipeline estimates based on:
- File count in storage bucket
- Average transcript size: 50KB per file
- Formula: `estimated_size = file_count * 50KB`

This is a conservative estimate to ensure we don't exceed the limit.

## Results When Stopped

When pipeline stops due to storage limit:

```python
{
    "stopped_reason": "Storage limit exceeded",
    "storage_info": {
        "current_usage_gb": 1.02,
        "limit_gb": 1.0,
        "usage_percent": 102.0
    },
    "processed_videos": 150,
    "failed_videos": 0
}
```

## Best Practices

1. **Monitor Regularly**: Check storage usage in Supabase dashboard
2. **Clean Up**: Delete old transcripts if needed
3. **Adjust Limit**: Set appropriate limit for your tier
4. **Process in Batches**: Process playlists in smaller batches

## Troubleshooting

### Pipeline Stops Too Early
- Check actual storage usage in Supabase dashboard
- Adjust estimation if transcripts are smaller/larger than 50KB average
- Increase `storage_limit_gb` if you have higher tier

### Pipeline Doesn't Stop
- Verify storage bucket exists and is accessible
- Check logs for storage check errors
- Manually verify storage usage in Supabase dashboard

## Status

- ✅ Storage monitoring implemented
- ✅ Automatic stop at limit
- ✅ Warning at 90% usage
- ✅ Graceful shutdown
- ✅ Progress saved when stopped

