#!/usr/bin/env python3
"""
Process specific YouTube channel: srichagantikoteswararaogar4451
Extracts playlists, processes videos, and stores transcripts in Supabase
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from playlist_pipeline import PlaylistTranscriptPipeline

# Load environment variables
load_dotenv()

# Channel URL
CHANNEL_URL = "https://www.youtube.com/@srichagantikoteswararaogar4451"

async def main():
    """Main entry point"""
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL", "https://jlfqzcaospvspmzbvbxd.supabase.co")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_key:
        print("Error: SUPABASE_KEY must be set in environment or .env file")
        sys.exit(1)
    
    # Initialize pipeline
    print(f"\n🚀 Initializing playlist pipeline...")
    print(f"   Channel: {CHANNEL_URL}")
    print(f"   Supabase URL: {supabase_url}\n")
    
    pipeline = PlaylistTranscriptPipeline(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        bucket_name="video-transcripts"
    )
    
    try:
        # Process channel playlists
        # Set max_playlists=None to process all playlists
        # Set max_videos_per_playlist=None to process all videos in each playlist
        results = await pipeline.process_channel_playlists(
            channel_url=CHANNEL_URL,
            max_playlists=None,  # Process all playlists
            max_videos_per_playlist=None,  # Process all videos
            delay_between_videos=3.0
        )
        
        # Print summary
        print("\n" + "="*60)
        print("PIPELINE SUMMARY")
        print("="*60)
        print(f"Total playlists found: {results['total_playlists']}")
        print(f"Playlists processed: {results['processed_playlists']}")
        print(f"Total videos processed: {results['processed_videos']}")
        print(f"Total videos failed: {results['failed_videos']}")
        print("="*60)
        
        # Print playlist details
        print("\nPlaylist Details:")
        for playlist_result in results['playlist_results']:
            print(f"\n  Playlist: {playlist_result['playlist_title']}")
            print(f"    Total videos: {playlist_result['total_videos']}")
            print(f"    Processed: {playlist_result['processed_videos']}")
            print(f"    Failed: {playlist_result['failed_videos']}")
            if playlist_result.get('status') != 'completed':
                print(f"    Status: {playlist_result.get('status', 'unknown')}")
        
        # Print failed videos if any
        if results['failed_videos'] > 0:
            print("\nFailed videos:")
            for playlist_result in results['playlist_results']:
                for video in playlist_result['videos']:
                    if video['status'] != 'success':
                        print(f"  - [{playlist_result['playlist_title']}] {video.get('video_title', 'Unknown')}: {video.get('error', 'Unknown error')}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user")
    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n✅ Pipeline completed")

if __name__ == "__main__":
    asyncio.run(main())

