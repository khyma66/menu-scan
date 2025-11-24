# Video Transcript Pipeline - Setup Guide

## Overview

This pipeline automates the extraction of YouTube video transcripts using NoteGPT.io and stores them in Supabase. It's designed to work with Supabase's free tier.

## Architecture

```
YouTube Channel → Extract URLs → NoteGPT.io → Extract Transcripts → Supabase Storage
                                                      ↓
                                            Supabase Database (metadata)
```

## Components

1. **YouTube Channel Extractor** (`youtube_channel_extractor.py`)
   - Extracts all video URLs from a YouTube channel
   - Uses `yt-dlp` library

2. **NoteGPT MCP Server** (`notegpt_mcp_server.py`)
   - MCP server that interacts with NoteGPT.io
   - Uses Playwright for browser automation
   - Extracts transcripts from YouTube URLs

3. **Transcript Pipeline** (`transcript_pipeline.py`)
   - Orchestrates the entire process
   - Stores transcripts in Supabase storage
   - Stores metadata in Supabase database

4. **Run Script** (`run_pipeline.py`)
   - Simple CLI interface for running the pipeline

## Installation

### 1. Install Python Dependencies

```bash
cd video-transcript-pipeline
pip install -r requirements.txt
```

### 2. Install Playwright Browser

```bash
playwright install chromium
```

### 3. Set Up Environment Variables

Create a `.env` file:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
```

### 4. Set Up Supabase

#### Create Storage Bucket

1. Go to Supabase Dashboard → Storage
2. Click "Create Bucket"
3. Name: `video-transcripts`
4. Public: **Yes** (required for free tier)
5. Click "Create"

#### Create Database Table

Run the SQL in `setup_supabase.sql` in your Supabase SQL Editor:

```sql
-- This creates the video_transcripts table and sets up RLS policies
-- See setup_supabase.sql for full SQL
```

#### Set Up Storage Policies

The SQL script also creates storage policies. If you need to create them manually:

1. Go to Storage → Policies
2. Select `video-transcripts` bucket
3. Create policies for:
   - Public read access
   - Authenticated upload
   - Authenticated update
   - Authenticated delete

## Usage

### Basic Usage

```bash
python run_pipeline.py "https://www.youtube.com/@channelname" 10
```

This will:
1. Extract 10 videos from the channel
2. Process each video through NoteGPT
3. Store transcripts in Supabase
4. Save metadata to database

### Interactive Mode

```bash
python run_pipeline.py
```

Follow the prompts to enter channel URL and max videos.

### Programmatic Usage

```python
from transcript_pipeline import TranscriptPipeline
import asyncio

async def main():
    pipeline = TranscriptPipeline(
        supabase_url="https://your-project.supabase.co",
        supabase_key="your-key"
    )
    
    results = await pipeline.process_channel(
        channel_url="https://www.youtube.com/@channelname",
        max_videos=5,
        delay_between_videos=3.0
    )
    
    print(f"Processed: {results['processed']}")
    print(f"Failed: {results['failed']}")

asyncio.run(main())
```

## MCP Server Integration

The MCP server is configured in `mcp.json` at the project root. After setup:

1. Restart Cursor/your IDE
2. The MCP server will be available with these tools:
   - `extract_transcript`: Extract transcript from a single YouTube URL
   - `batch_extract_transcripts`: Extract transcripts from multiple URLs

## Free Tier Considerations

### Supabase Free Tier Limits
- **Database**: 500 MB
- **Storage**: 1 GB
- **Bandwidth**: 2 GB/month

### Storage Strategy
- Full transcripts stored in storage bucket (as text files)
- First 5000 characters stored in database for quick access
- Metadata (title, URL, etc.) stored in database

### Rate Limiting
- Default delay: 3 seconds between videos
- Adjustable via `delay_between_videos` parameter
- NoteGPT may have usage limits (check their website)

## Troubleshooting

### Browser Issues
- Ensure Playwright is installed: `playwright install chromium`
- If headless mode fails, check browser logs
- Try running with visible browser (modify code)

### Supabase Issues
- Verify bucket exists and is public
- Check API key has storage permissions
- Verify RLS policies are correct
- Check storage policies allow uploads

### NoteGPT Issues
- Website structure may change - update selectors if needed
- Check for rate limiting
- Verify YouTube URL format

### YouTube Extraction Issues
- Ensure `yt-dlp` is up to date: `pip install --upgrade yt-dlp`
- Some channels may have restrictions
- Check network connectivity

## File Structure

```
video-transcript-pipeline/
├── notegpt_mcp_server.py      # MCP server for NoteGPT
├── youtube_channel_extractor.py # YouTube URL extractor
├── transcript_pipeline.py      # Main pipeline
├── run_pipeline.py             # CLI runner
├── setup_supabase.sql          # Database schema
├── requirements.txt            # Python dependencies
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
├── README.md                  # Main documentation
├── QUICK_START.md            # Quick start guide
└── SETUP.md                   # This file
```

## Next Steps

1. Test with a small channel (1-2 videos)
2. Verify transcripts in Supabase storage
3. Check database table for metadata
4. Scale up to larger channels
5. Integrate with your application

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs for error messages
3. Verify all dependencies are installed
4. Ensure Supabase is configured correctly

