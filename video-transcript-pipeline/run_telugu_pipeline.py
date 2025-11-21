"""
Run Telugu transcription pipeline for the specified channel
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

from telugu_transcription_pipeline import TeluguTranscriptionPipeline

load_dotenv()


async def main():
    """Main entry point"""
    supabase_url = os.getenv("SUPABASE_URL", "https://jlfqzcaospvspmzbvbxd.supabase.co")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_key:
        print("Error: SUPABASE_KEY must be set")
        sys.exit(1)
    
    print("="*60)
    print("Telugu Video Transcription Pipeline")
    print("="*60)
    print(f"Supabase URL: {supabase_url}")
    print(f"Whisper Model: base")
    print(f"Language: Telugu (te)")
    print("="*60)
    
    pipeline = TeluguTranscriptionPipeline(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        whisper_model="large-v3",  # Best accuracy for Telugu - 3GB download
        language="te"  # Telugu
    )
    
    channel_url = "https://www.youtube.com/@srichagantikoteswararaogar4451"
    
    print(f"\nProcessing channel: {channel_url}")
    print("Starting with 1 playlist and 1 video for testing...")
    print("(Adjust max_playlists and max_videos_per_playlist to process more)\n")
    
    results = await pipeline.process_channel(
        channel_url=channel_url,
        max_playlists=1,  # Start with 1 playlist for testing
        max_videos_per_playlist=1  # Start with 1 video for testing
    )
    
    print("\n" + "="*60)
    print("PIPELINE COMPLETE")
    print("="*60)
    print(f"Total Playlists: {results['total_playlists']}")
    print(f"Processed Videos: {results['processed_videos']}")
    print(f"Failed Videos: {results['failed_videos']}")
    print("="*60)
    
    # Print playlist results
    for playlist_result in results['playlist_results']:
        print(f"\nPlaylist: {playlist_result['playlist_title']}")
        print(f"  Total Videos: {playlist_result['total_videos']}")
        print(f"  Processed: {playlist_result['processed']}")
        print(f"  Failed: {playlist_result['failed']}")


if __name__ == "__main__":
    asyncio.run(main())

