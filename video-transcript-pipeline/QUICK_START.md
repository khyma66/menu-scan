# Quick Start Guide - Video Transcript Pipeline

## Prerequisites

1. Python 3.9+
2. Supabase account (free tier)
3. Playwright browser installed

## Setup Steps

### 1. Install Dependencies

```bash
cd video-transcript-pipeline
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure Environment

Create a `.env` file:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
```

### 3. Set Up Supabase

#### Option A: Using Supabase Dashboard (Recommended for Free Tier)

1. Go to your Supabase project dashboard
2. Navigate to **Storage** → **Create Bucket**
3. Name: `video-transcripts`
4. Public: **Yes** (for free tier access)
5. Click **Create**

#### Option B: Using SQL (Requires Service Role Key)

Run the SQL script in Supabase SQL Editor:

```bash
# Copy contents of setup_supabase.sql and run in Supabase SQL Editor
```

### 4. Run the Pipeline

```bash
# Basic usage
python run_pipeline.py "https://www.youtube.com/@channelname" 10

# Or interactive mode
python run_pipeline.py
```

## Example Usage

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
        max_videos=5
    )
    
    print(f"Processed: {results['processed']}")

asyncio.run(main())
```

## MCP Server Usage

The MCP server is configured in `mcp.json`. To use it:

1. Restart Cursor/your IDE to load the new MCP server
2. The server provides two tools:
   - `extract_transcript`: Extract transcript from a single YouTube URL
   - `batch_extract_transcripts`: Extract transcripts from multiple URLs

## Troubleshooting

### Browser Issues
- Make sure Playwright is installed: `playwright install chromium`
- If headless mode fails, try running with visible browser (modify code)

### Supabase Issues
- Ensure bucket exists and is public
- Check that your API key has storage permissions
- Verify RLS policies are set correctly

### Rate Limiting
- Increase `delay_between_videos` if you hit rate limits
- NoteGPT may have usage limits on free tier

## Free Tier Limits

- **Supabase**: 500 MB database, 1 GB storage, 2 GB bandwidth
- **NoteGPT**: Check their website for current limits
- **YouTube**: No official API limits for public videos

## Next Steps

1. Process your first channel
2. Check Supabase storage for transcripts
3. Query the `video_transcripts` table for metadata
4. Integrate with your application

