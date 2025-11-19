#!/usr/bin/env python3
"""
Test script to process a single video URL and verify it stores in database
"""

import asyncio
import os
import sys
from supabase import create_client
from dotenv import load_dotenv
from notegpt_mcp_server import extract_transcript
from datetime import datetime

load_dotenv()

async def test_single_video():
    """Test processing a single video"""
    supabase_url = os.getenv("SUPABASE_URL", "https://jlfqzcaospvspmzbvbxd.supabase.co")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_key:
        print("Error: SUPABASE_KEY must be set")
        sys.exit(1)
    
    client = create_client(supabase_url, supabase_key)
    
    # Test with a single video URL
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Example URL
    
    print(f"Testing with URL: {test_url}")
    print("Step 1: Extracting transcript from NoteGPT...")
    
    try:
        # Extract transcript
        result = await extract_transcript(test_url)
        
        if not result.get("success"):
            print(f"❌ Failed to extract transcript: {result.get('error')}")
            return
        
        video_title = result.get("title", "Test Video")
        transcript_text = result.get("transcript", "")
        video_id = test_url.split("v=")[-1].split("&")[0] if "v=" in test_url else "test"
        
        print(f"✓ Got transcript: {video_title}")
        print(f"  Length: {len(transcript_text)} characters")
        print(f"  Preview: {transcript_text[:200]}...")
        
        # Store in database
        print("\nStep 2: Storing in database...")
        
        insert_data = {
            "playlist_id": "test_playlist",
            "playlist_title": "Test Playlist",
            "video_id": video_id,
            "youtube_url": test_url,
            "title": video_title,
            "transcript": transcript_text[:5000],
            "storage_path": f"test/{video_id}.txt",
            "storage_url": f"{supabase_url}/storage/v1/object/public/video-transcripts/test/{video_id}.txt",
            "metadata": {
                "extracted_at": result.get("extracted_at"),
                "transcript_length": len(transcript_text),
                "test": True
            }
        }
        
        db_result = client.table("playlist_transcripts").insert(insert_data).execute()
        
        print(f"✓ Stored in database!")
        print(f"  ID: {db_result.data[0]['id'] if db_result.data else 'N/A'}")
        
        # Verify it's in database
        print("\nStep 3: Verifying in database...")
        verify = client.table("playlist_transcripts").select("*").eq("video_id", video_id).execute()
        
        if verify.data:
            print(f"✓ Verified! Found {len(verify.data)} record(s)")
            print(f"  Title: {verify.data[0]['title']}")
            print(f"  Transcript length: {len(verify.data[0].get('transcript', ''))}")
        else:
            print("❌ Not found in database!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_single_video())

