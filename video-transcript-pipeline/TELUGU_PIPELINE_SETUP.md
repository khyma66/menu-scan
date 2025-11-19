# Telugu Video Auto Transcription Pipeline

## Overview

This pipeline uses **Whisper ASR** + **LLM Enhancement** for Telugu video transcription, following the workflow:

1. Extract Audio from Video (FFmpeg)
2. Automatic Speech Recognition (Whisper - Telugu support)
3. Post-Process with LLM (punctuation, corrections)
4. Generate Subtitle Files (SRT/VTT)
5. Store in Supabase

## Setup

### 1. Install System Dependencies

```bash
# Install FFmpeg (required for audio extraction)
brew install ffmpeg

# Verify installation
ffmpeg -version
```

### 2. Install Python Dependencies

```bash
cd video-transcript-pipeline
source venv/bin/activate
pip install -r requirements_telugu.txt
```

### 3. Set Up Database

Run `setup_telugu_transcripts.sql` in Supabase SQL Editor to create the table.

### 4. Configure Environment

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key

# Optional: For LLM enhancement
OPENAI_API_KEY=your-openai-key
# OR
ANTHROPIC_API_KEY=your-anthropic-key
```

## Usage

### Process Single Video

```python
from telugu_transcription_pipeline import TeluguTranscriptionPipeline

pipeline = TeluguTranscriptionPipeline(
    supabase_url="https://your-project.supabase.co",
    supabase_key="your-key",
    whisper_model="base",  # or "large" for better accuracy
    language="te"  # Telugu
)

result = await pipeline.process_video(
    youtube_url="https://www.youtube.com/watch?v=VIDEO_ID",
    video_title="Video Title",
    video_id="VIDEO_ID"
)
```

### Process Channel Playlists

```python
results = await pipeline.process_channel(
    channel_url="https://www.youtube.com/@channelname",
    max_playlists=5,
    max_videos_per_playlist=10
)
```

## Process Flow

### Step 1: Extract Audio
```bash
yt-dlp -x --audio-format wav --audio-quality 0 -o output.wav VIDEO_URL
```

### Step 2: Whisper ASR
- Loads Whisper model (base/large)
- Transcribes audio in Telugu
- Returns text with timestamps

### Step 3: LLM Enhancement
- Adds punctuation
- Corrects misheard words
- Improves formatting
- Uses GPT-4o-mini or Claude

### Step 4: Generate Subtitles
- Creates SRT file (with timestamps)
- Creates VTT file (web format)
- Stores in Supabase storage

### Step 5: Store in Database
- Raw transcript (from Whisper)
- Enhanced transcript (from LLM)
- Subtitle files (SRT/VTT)
- Metadata (language, model, duration)

## Database Schema

### `telugu_transcripts` Table

- `video_id` - YouTube video ID (unique)
- `youtube_url` - Full URL
- `title` - Video title
- `raw_transcript` - Whisper output (first 10K chars)
- `enhanced_transcript` - LLM-enhanced (first 10K chars)
- `srt_storage_path` - Path to SRT file
- `vtt_storage_path` - Path to VTT file
- `srt_url` - Public URL to SRT
- `vtt_url` - Public URL to VTT
- `segments_count` - Number of subtitle segments
- `metadata` - JSONB with processing info

## Whisper Models

- `tiny` - Fastest, least accurate
- `base` - Balanced (recommended)
- `small` - Better accuracy
- `medium` - High accuracy
- `large` - Best accuracy (slower)

For Telugu, `base` or `large` recommended.

## Storage Structure

```
video-transcripts/
└── playlists/
    └── {playlist_id}/
        ├── {video_id}.srt          # Subtitle file
        ├── {video_id}.vtt          # Web subtitle file
        └── {video_id}_transcript.txt  # Full transcript
```

## Features

- ✅ Telugu language support
- ✅ Automatic audio extraction
- ✅ Whisper ASR transcription
- ✅ LLM enhancement (optional)
- ✅ SRT/VTT subtitle generation
- ✅ Timestamp synchronization
- ✅ Supabase storage integration

## Example Output

### SRT Format
```
1
00:00:00,000 --> 00:00:05,000
వీడియో ట్రాన్స్క్రిప్ట్

2
00:00:05,000 --> 00:00:10,000
ఇది తెలుగు భాషలో వ్రాయబడింది
```

### Enhanced Transcript
```
వీడియో ట్రాన్స్క్రిప్ట్. ఇది తెలుగు భాషలో వ్రాయబడింది.
```

## Troubleshooting

### FFmpeg Not Found
```bash
brew install ffmpeg
```

### Whisper Model Download
First run will download the model (~150MB-3GB depending on size)

### LLM Enhancement Fails
Pipeline continues without enhancement if LLM API unavailable

### Audio Download Fails
Check YouTube URL validity and network connectivity

## Performance

- **Audio Extraction**: ~30 seconds per video
- **Whisper Transcription**: ~1-5 minutes (depends on model)
- **LLM Enhancement**: ~5-10 seconds
- **Total**: ~2-6 minutes per video

## Next Steps

1. Install dependencies
2. Set up database table
3. Run pipeline on test video
4. Scale to full channel processing

