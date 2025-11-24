#!/usr/bin/env python3
"""
Test with one actual video from the channel to verify end-to-end
"""

import os
import sys
from supabase import create_client
from youtube_playlist_extractor import YouTubePlaylistExtractor
from youtube_transcript_extractor import extract_youtube_transcript
from datetime import datetime

CHANNEL_URL = "https://www.youtube.com/@srichagantikoteswararaogar4451"

def main():
    supabase_url = "https://jlfqzcaospvspmzbvbxd.supabase.co"
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpsZnF6Y2Fvc3B2c3BtemJ2YnhkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEzNzAzMzYsImV4cCI6MjA3Njk0NjMzNn0.cTI-Zo2NXeIZQDiQ4mcLia3slwRMyvMLpLj_-4BtviA"
    
    client = create_client(supabase_url, supabase_key)
    
    print("Getting playlists from channel...")
    extractor = YouTubePlaylistExtractor()
    playlists = extractor.get_channel_playlists(CHANNEL_URL)
    
    if not playlists:
        print("No playlists found!")
        return
    
    print(f"Found {len(playlists)} playlists")
    print(f"Testing with first playlist: {playlists[0]['title']}")
    
    # Get videos from first playlist - try multiple to find one with transcript
    videos = extractor.get_playlist_videos(playlists[0]['url'], max_results=5)
    
    if not videos:
        print("No videos found in playlist!")
        return
    
    # Try each video until we find one with transcript
    result = None
    test_video = None
    
    for video in videos:
        print(f"\nTrying video: {video['title']}")
        print(f"URL: {video['url']}")
        
        # Extract transcript
        print("Extracting transcript...")
        result = extract_youtube_transcript(video['url'])
        
        if result.get("success") and len(result.get("transcript", "")) > 100:
            test_video = video
            print(f"✓ Found video with transcript!")
            break
        else:
            print(f"✗ No transcript available, trying next video...")
    
    if not result or not result.get("success") or not test_video:
        print("\n✗ Could not find any video with transcript in first playlist")
        print("Note: Some videos may not have transcripts available")
        return
    
    video_title = result.get("title")
    transcript_text = result.get("transcript", "")
    video_id = test_video.get('video_id', '')
    
    print(f"✓ Got transcript: {video_title}")
    print(f"  Length: {len(transcript_text)} characters")
    print(f"  Preview: {transcript_text[:200]}...")
    
    # Store in database
    print("\nStoring in database...")
    insert_data = {
        "playlist_id": playlists[0]['playlist_id'],
        "playlist_title": playlists[0]['title'],
        "video_id": video_id,
        "youtube_url": test_video['url'],
        "title": video_title,
        "transcript": transcript_text[:5000],
        "storage_path": f"playlists/{playlists[0]['playlist_id']}/{video_id}.txt",
        "storage_url": f"{supabase_url}/storage/v1/object/public/video-transcripts/playlists/{playlists[0]['playlist_id']}/{video_id}.txt",
        "metadata": {
            "extracted_at": result.get("extracted_at"),
            "transcript_length": len(transcript_text)
        }
    }
    
    try:
        db_result = client.table("playlist_transcripts").insert(insert_data).execute()
        print(f"✓ Stored! ID: {db_result.data[0]['id'] if db_result.data else 'N/A'}")
        
        # Verify
        verify = client.table("playlist_transcripts").select("*").eq("video_id", video_id).execute()
        if verify.data:
            print(f"✓ Verified! Found in database")
            print(f"  Title: {verify.data[0]['title']}")
            print(f"  Transcript length: {len(verify.data[0].get('transcript', ''))}")
        else:
            print("✗ Not found in database!")
            
    except Exception as e:
        print(f"✗ Database error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

