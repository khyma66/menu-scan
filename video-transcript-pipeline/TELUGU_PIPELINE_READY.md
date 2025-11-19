# Telugu Video Transcription Pipeline - Ready to Use

## ✅ Completed Setup

1. **Old tables deleted**: `playlist_transcripts` and `playlists` tables removed
2. **New table created**: `telugu_transcripts` table in Supabase
3. **Pipeline implemented**: Complete Whisper ASR + LLM enhancement workflow
4. **Database schema**: Ready for storing Telugu video transcripts

## 📋 Current Status

- ✅ Database table: `telugu_transcripts` (created)
- ✅ Pipeline code: `telugu_transcription_pipeline.py`
- ✅ FFmpeg: Installed (`/opt/homebrew/bin/ffmpeg`)
- ⚠️ Whisper: Needs Python 3.13 (current venv uses Python 3.14)

## 🚀 Quick Start

### Step 1: Create Python 3.13 Virtual Environment

```bash
cd video-transcript-pipeline

# Remove old venv if needed
rm -rf venv

# Create new venv with Python 3.13
python3.13 -m venv venv
source venv/bin/activate

# Verify Python version
python --version  # Should show Python 3.13.x
```

### Step 2: Install Dependencies

```bash
# Install core dependencies
pip install -r requirements_telugu.txt

# If Whisper fails, install directly:
pip install git+https://github.com/openai/whisper.git
```

### Step 3: Set Environment Variables

```bash
export SUPABASE_URL="https://jlfqzcaospvspmzbvbxd.supabase.co"
export SUPABASE_KEY="your-supabase-key"

# Optional: For LLM enhancement
export OPENAI_API_KEY="your-openai-key"
```

### Step 4: Run Pipeline

```bash
# Test with single video
python test_telugu_pipeline.py

# Run full pipeline
python run_telugu_pipeline.py
```

## 📊 Pipeline Workflow

```
YouTube Video
    ↓
[1] Extract Audio (yt-dlp + FFmpeg)
    ↓
[2] Whisper ASR (Telugu transcription)
    ↓
[3] LLM Enhancement (punctuation, corrections)
    ↓
[4] Generate Subtitles (SRT/VTT)
    ↓
[5] Store in Supabase
```

## 🗄️ Database Schema

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

## 📁 Storage Structure

```
video-transcripts/
└── playlists/
    └── {playlist_id}/
        ├── {video_id}.srt
        ├── {video_id}.vtt
        └── {video_id}_transcript.txt
```

## 🔧 Configuration

Edit `run_telugu_pipeline.py` to adjust:

- `whisper_model`: "base" (faster) or "large" (more accurate)
- `max_playlists`: Number of playlists to process
- `max_videos_per_playlist`: Videos per playlist

## 📝 Example Usage

```python
from telugu_transcription_pipeline import TeluguTranscriptionPipeline

pipeline = TeluguTranscriptionPipeline(
    supabase_url="https://your-project.supabase.co",
    supabase_key="your-key",
    whisper_model="base",
    language="te"
)

# Process single video
result = await pipeline.process_video(
    youtube_url="https://www.youtube.com/watch?v=VIDEO_ID",
    video_title="Video Title",
    video_id="VIDEO_ID"
)

# Process channel
results = await pipeline.process_channel(
    channel_url="https://www.youtube.com/@channelname",
    max_playlists=5,
    max_videos_per_playlist=10
)
```

## ⚠️ Important Notes

1. **Python Version**: Requires Python 3.10-3.13 (not 3.14+)
2. **FFmpeg**: Must be installed system-wide
3. **Whisper Models**: First run downloads model (~150MB-3GB)
4. **Processing Time**: ~2-6 minutes per video
5. **Storage**: Full transcripts stored in Supabase storage bucket

## 🐛 Troubleshooting

### Python Version Issue
```bash
# Use Python 3.13
python3.13 -m venv venv
source venv/bin/activate
```

### Whisper Installation Fails
```bash
pip install git+https://github.com/openai/whisper.git
```

### FFmpeg Not Found
```bash
brew install ffmpeg
```

## 📚 Files

- `telugu_transcription_pipeline.py` - Main pipeline
- `run_telugu_pipeline.py` - Runner script
- `test_telugu_pipeline.py` - Test script
- `setup_telugu_transcripts.sql` - Database schema
- `TELUGU_PIPELINE_SETUP.md` - Detailed setup guide

## ✅ Next Steps

1. Create Python 3.13 virtual environment
2. Install dependencies
3. Run test script
4. Process full channel

