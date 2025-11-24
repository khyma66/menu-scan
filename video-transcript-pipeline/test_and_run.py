#!/usr/bin/env python3
"""
Test and run pipeline with a single video first to verify everything works
"""

import asyncio
import os
import sys
from supabase import create_client
from dotenv import load_dotenv
from youtube_playlist_extractor import YouTubePlaylistExtractor
from youtube_transcript_extractor import extract_youtube_transcript
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

CHANNEL_URL = "https://www.youtube.com/@srichagantikoteswararaogar4451"

async def process_and_store_video(youtube_url: str, supabase_client, playlist_id: str, playlist_title: str):
    """Process one video and store in database"""
    try:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {youtube_url}")
        logger.info(f"{'='*60}")
        
        # Extract transcript from YouTube
        logger.info("Extracting transcript from YouTube...")
        transcript_result = extract_youtube_transcript(youtube_url)
        
        if not transcript_result.get("success"):
            logger.error(f"Failed: {transcript_result.get('error')}")
            return {"success": False, "error": transcript_result.get("error")}
        
        video_title = transcript_result.get("title", "Untitled")
        transcript_text = transcript_result.get("transcript", "")
        video_id = youtube_url.split("v=")[-1].split("&")[0] if "v=" in youtube_url else ""
        
        logger.info(f"✓ Got transcript: {video_title}")
        logger.info(f"  Length: {len(transcript_text)} characters")
        
        if len(transcript_text) < 50:
            logger.warning("Transcript too short, might be invalid")
            return {"success": False, "error": "Transcript too short"}
        
        # Store in database
        logger.info("Storing in database...")
        
        insert_data = {
            "playlist_id": playlist_id,
            "playlist_title": playlist_title,
            "video_id": video_id,
            "youtube_url": youtube_url,
            "title": video_title,
            "transcript": transcript_text[:5000],  # First 5000 chars
            "storage_path": f"playlists/{playlist_id}/{video_id}.txt",
            "storage_url": f"https://jlfqzcaospvspmzbvbxd.supabase.co/storage/v1/object/public/video-transcripts/playlists/{playlist_id}/{video_id}.txt",
            "metadata": {
                "extracted_at": transcript_result.get("extracted_at"),
                "transcript_length": len(transcript_text),
                "method": transcript_result.get("method", "youtube_direct")
            }
        }
        
        # Insert into database
        db_result = supabase_client.table("playlist_transcripts").insert(insert_data).execute()
        
        logger.info(f"✓ Stored in database! ID: {db_result.data[0]['id'] if db_result.data else 'N/A'}")
        
        # Store full transcript in storage
        try:
            safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
            filename = f"playlists/{playlist_id}/{video_id}_{safe_title}.txt"
            
            supabase_client.storage.from_("video-transcripts").upload(
                filename,
                transcript_text.encode('utf-8'),
                file_options={"content-type": "text/plain", "upsert": "true"}
            )
            
            logger.info(f"✓ Stored in storage: {filename}")
        except Exception as storage_error:
            logger.warning(f"Storage upload failed: {storage_error}")
        
        return {
            "success": True,
            "video_id": video_id,
            "title": video_title,
            "transcript_length": len(transcript_text)
        }
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

async def main():
    """Main function"""
    supabase_url = os.getenv("SUPABASE_URL", "https://jlfqzcaospvspmzbvbxd.supabase.co")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_key:
        print("Error: SUPABASE_KEY must be set")
        sys.exit(1)
    
    client = create_client(supabase_url, supabase_key)
    
    print("\n" + "="*60)
    print("VIDEO TRANSCRIPT PIPELINE")
    print("="*60)
    print(f"Channel: {CHANNEL_URL}")
    print("="*60 + "\n")
    
    # Get playlists
    extractor = YouTubePlaylistExtractor()
    print("Step 1: Extracting playlists...")
    playlists = extractor.get_channel_playlists(CHANNEL_URL)
    print(f"Found {len(playlists)} playlists\n")
    
    total_processed = 0
    total_failed = 0
    
    # Process each playlist
    for playlist_idx, playlist in enumerate(playlists, 1):
        print(f"\n{'='*60}")
        print(f"Playlist {playlist_idx}/{len(playlists)}: {playlist['title']}")
        print(f"{'='*60}")
        
        # Get videos
        videos = extractor.get_playlist_videos(playlist['url'])
        print(f"Found {len(videos)} videos\n")
        
        # Process each video
        for video_idx, video in enumerate(videos, 1):
            print(f"\n[{video_idx}/{len(videos)}] Video: {video['title']}")
            
            result = await process_and_store_video(
                video['url'],
                client,
                playlist['playlist_id'],
                playlist['title']
            )
            
            if result.get("success"):
                total_processed += 1
                print(f"✓ Success!")
            else:
                total_failed += 1
                print(f"✗ Failed: {result.get('error')}")
            
            # Delay between videos
            if video_idx < len(videos):
                await asyncio.sleep(2)
        
        # Update playlist metadata
        try:
            client.table("playlists").upsert({
                "playlist_id": playlist['playlist_id'],
                "title": playlist['title'],
                "url": playlist['url'],
                "video_count": len(videos),
                "processed_videos": total_processed,
                "failed_videos": total_failed,
                "status": "completed"
            }).execute()
        except Exception as e:
            logger.warning(f"Could not update playlist: {e}")
    
    # Final summary
    print("\n" + "="*60)
    print("PIPELINE COMPLETE")
    print("="*60)
    print(f"Total playlists: {len(playlists)}")
    print(f"Videos processed: {total_processed}")
    print(f"Videos failed: {total_failed}")
    print("="*60)
    
    # Verify in database
    verify = client.table("playlist_transcripts").select("COUNT").execute()
    print(f"\nTotal transcripts in database: {verify.count if hasattr(verify, 'count') else 'Check manually'}")

if __name__ == "__main__":
    asyncio.run(main())

