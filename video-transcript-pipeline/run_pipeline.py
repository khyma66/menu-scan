#!/usr/bin/env python3
"""
Simple script to run the video transcript pipeline
Usage: python run_pipeline.py <youtube_channel_url> [max_videos]
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from transcript_pipeline import TranscriptPipeline

# Load environment variables
load_dotenv()

async def main():
    """Main entry point"""
    # Get channel URL from command line or input
    if len(sys.argv) > 1:
        channel_url = sys.argv[1]
    else:
        channel_url = input("Enter YouTube channel URL: ")
    
    # Get max videos from command line or input
    if len(sys.argv) > 2:
        try:
            max_videos = int(sys.argv[2])
        except ValueError:
            max_videos = None
    else:
        max_input = input("Max videos to process (press Enter for all): ").strip()
        max_videos = int(max_input) if max_input else None
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set in environment or .env file")
        sys.exit(1)
    
    # Initialize pipeline
    print(f"\n🚀 Initializing pipeline...")
    print(f"   Channel: {channel_url}")
    print(f"   Max videos: {max_videos or 'All'}")
    print(f"   Supabase URL: {supabase_url}\n")
    
    pipeline = TranscriptPipeline(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        bucket_name="video-transcripts"
    )
    
    try:
        # Process channel
        results = await pipeline.process_channel(
            channel_url=channel_url,
            max_videos=max_videos,
            delay_between_videos=3.0
        )
        
        # Print summary
        print("\n" + "="*60)
        print("PIPELINE SUMMARY")
        print("="*60)
        print(f"Total videos found: {results['total_videos']}")
        print(f"Successfully processed: {results['processed']}")
        print(f"Failed: {results['failed']}")
        print("="*60)
        
        # Print failed videos if any
        if results['failed'] > 0:
            print("\nFailed videos:")
            for result in results['results']:
                if result['status'] != 'success':
                    print(f"  - {result.get('video_title', 'Unknown')}: {result.get('error', 'Unknown error')}")
        
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

