# Video Transcript Pipeline

Automated pipeline for extracting YouTube video transcripts using NoteGPT and storing them in Supabase.

## Features

- Extract video URLs from YouTube channels
- Automatically extract transcripts using NoteGPT.io
- Store transcripts in Supabase storage (free tier compatible)
- Store metadata in Supabase database
- Batch processing with rate limiting

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure Environment Variables

Create a `.env` file:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
```

### 3. Set Up Supabase

1. Run the SQL script to create the table and policies:
   ```bash
   # In Supabase SQL Editor, run:
   psql -h your-db-host -U postgres -d postgres -f setup_supabase.sql
   ```

2. Create the storage bucket manually in Supabase Dashboard:
   - Go to Storage → Create Bucket
   - Name: `video-transcripts`
   - Public: Yes (for free tier)

### 4. Configure MCP Server

The MCP server is configured in `mcp.json` at the project root.

## Usage

### Basic Usage

```python
from transcript_pipeline import TranscriptPipeline
import asyncio

async def main():
    pipeline = TranscriptPipeline(
        supabase_url="https://your-project.supabase.co",
        supabase_key="your-key",
        bucket_name="video-transcripts"
    )
    
    results = await pipeline.process_channel(
        channel_url="https://www.youtube.com/@channelname",
        max_videos=10,  # None for all videos
        delay_between_videos=3.0  # seconds
    )
    
    print(f"Processed: {results['processed']}, Failed: {results['failed']}")

asyncio.run(main())
```

### Command Line Usage

```bash
python transcript_pipeline.py
```

### Extract Channel Videos Only

```bash
python youtube_channel_extractor.py
```

## MCP Server

The MCP server provides tools for extracting transcripts:

- `extract_transcript`: Extract transcript from a single YouTube URL
- `batch_extract_transcripts`: Extract transcripts from multiple URLs

## Project Structure

```
video-transcript-pipeline/
├── notegpt_mcp_server.py      # MCP server for NoteGPT integration
├── youtube_channel_extractor.py # Extract videos from YouTube channels
├── transcript_pipeline.py      # Main automation pipeline
├── setup_supabase.sql          # Database schema and policies
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Free Tier Considerations

- Supabase free tier includes:
  - 500 MB database storage
  - 1 GB file storage
  - 2 GB bandwidth
  
- The pipeline stores:
  - Transcript text files in storage bucket
  - Metadata in database table
  - First 5000 chars of transcript in database for quick access

## Rate Limiting

The pipeline includes delays between requests to avoid:
- YouTube API rate limits
- NoteGPT rate limits
- Supabase rate limits

Default delay: 3 seconds between videos

## Error Handling

The pipeline handles:
- Network errors
- Missing videos
- Extraction failures
- Storage failures

All errors are logged and included in the results.

## License

MIT

