# Pipeline Monitoring

## Current Status

**Pipeline Running**: ✅ Active
**Channel**: @srichagantikoteswararaogar4451
**Total Playlists Found**: 136
**Processing**: 1 playlist, 1 video (test mode)

## Progress Tracking

Monitor the pipeline with:
```bash
tail -f video-transcript-pipeline/pipeline_run.log
```

## Expected Steps

1. ✅ Extract playlists from channel
2. ⏳ Download audio from video
3. ⏳ Transcribe with Whisper large-v3
4. ⏳ Generate subtitle files
5. ⏳ Store in Supabase

## Processing Time

- Audio extraction: ~1-2 minutes
- Transcription (large-v3): ~10-15 minutes per 10-minute video
- Total per video: ~15-20 minutes

## Check Results

```bash
# Check stored transcripts
cd video-transcript-pipeline
source venv/bin/activate
python -c "
from supabase import create_client
import os
from dotenv import load_dotenv
load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
result = supabase.table('telugu_transcripts').select('*').order('created_at', desc=True).limit(5).execute()
print(result.data)
"
```

