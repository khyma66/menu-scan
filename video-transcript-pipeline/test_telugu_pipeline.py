"""
Test script for Telugu transcription pipeline
Tests a single video to verify the complete workflow
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

from telugu_transcription_pipeline import TeluguTranscriptionPipeline

load_dotenv()


async def test_single_video():
    """Test processing a single Telugu video"""
    supabase_url = os.getenv("SUPABASE_URL", "https://jlfqzcaospvspmzbvbxd.supabase.co")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_key:
        print("Error: SUPABASE_KEY must be set")
        sys.exit(1)
    
    print("="*60)
    print("Testing Telugu Transcription Pipeline")
    print("="*60)
    
    # Initialize pipeline
    pipeline = TeluguTranscriptionPipeline(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        whisper_model="base",  # Start with base model
        language="te"  # Telugu
    )
    
    # Test with a single video from the channel
    test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Replace with actual Telugu video
    
    print(f"\nProcessing test video...")
    print(f"URL: {test_video_url}")
    
    result = await pipeline.process_video(
        youtube_url=test_video_url,
        video_title="Test Telugu Video",
        video_id="test_video_001"
    )
    
    if result.get("success"):
        print("\n✓ SUCCESS!")
        print(f"  Video ID: {result.get('video_id')}")
        print(f"  Title: {result.get('title')}")
        print(f"  Transcript Length: {result.get('transcript_length')} characters")
        print(f"  Segments: {result.get('segments_count')}")
    else:
        print("\n✗ FAILED")
        print(f"  Error: {result.get('error')}")
    
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_single_video())


