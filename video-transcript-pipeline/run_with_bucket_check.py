#!/usr/bin/env python3
"""
Run pipeline with automatic bucket creation check
"""

import asyncio
import os
import sys
from supabase import create_client
from dotenv import load_dotenv
from playlist_pipeline import PlaylistTranscriptPipeline

load_dotenv()

CHANNEL_URL = "https://www.youtube.com/@srichagantikoteswararaogar4451"

async def check_and_create_bucket():
    """Check if bucket exists, create if needed"""
    supabase_url = os.getenv("SUPABASE_URL", "https://jlfqzcaospvspmzbvbxd.supabase.co")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_key:
        print("Error: SUPABASE_KEY must be set")
        sys.exit(1)
    
    client = create_client(supabase_url, supabase_key)
    bucket_name = "video-transcripts"
    
    try:
        buckets = client.storage.list_buckets()
        bucket_names = [b.name for b in buckets]
        
        if bucket_name in bucket_names:
            print(f"✅ Bucket '{bucket_name}' exists")
            return True
        else:
            print(f"❌ Bucket '{bucket_name}' not found")
            print("\nPlease create the bucket manually:")
            print(f"  1. Go to: https://supabase.com/dashboard/project/jlfqzcaospvspmzbvbxd/storage/buckets")
            print(f"  2. Click 'New bucket'")
            print(f"  3. Name: {bucket_name}")
            print(f"  4. Public: Yes")
            print(f"  5. Click 'Create bucket'")
            print("\nThen run this script again.")
            return False
    except Exception as e:
        print(f"Error checking bucket: {e}")
        return False

async def main():
    """Main entry point"""
    print("🔍 Checking storage bucket...")
    
    bucket_exists = await check_and_create_bucket()
    
    if not bucket_exists:
        print("\n⚠️  Cannot proceed without bucket. Please create it first.")
        sys.exit(1)
    
    print("\n🚀 Starting pipeline...")
    
    supabase_url = os.getenv("SUPABASE_URL", "https://jlfqzcaospvspmzbvbxd.supabase.co")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    pipeline = PlaylistTranscriptPipeline(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        bucket_name="video-transcripts",
        storage_limit_gb=1.0
    )
    
    print(f"   Channel: {CHANNEL_URL}")
    print(f"   Storage limit: 1.0 GB")
    print(f"   Storage monitoring: Enabled\n")
    
    try:
        results = await pipeline.process_channel_playlists(
            channel_url=CHANNEL_URL,
            max_playlists=None,
            max_videos_per_playlist=None,
            delay_between_videos=3.0
        )
        
        print("\n" + "="*60)
        print("PIPELINE SUMMARY")
        print("="*60)
        print(f"Total playlists found: {results['total_playlists']}")
        print(f"Playlists processed: {results['processed_playlists']}")
        print(f"Total videos processed: {results['processed_videos']}")
        print(f"Total videos failed: {results['failed_videos']}")
        
        if results.get('stopped_reason') == 'Storage limit exceeded':
            print(f"\n⚠️  Pipeline stopped: {results['stopped_reason']}")
            storage_info = results.get('storage_info', {})
            if storage_info:
                print(f"   Current usage: {storage_info.get('current_usage_gb', 0):.2f} GB")
                print(f"   Limit: {storage_info.get('limit_gb', 1.0):.2f} GB")
                print(f"   Usage: {storage_info.get('usage_percent', 0):.1f}%")
        
        print("="*60)
        
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

