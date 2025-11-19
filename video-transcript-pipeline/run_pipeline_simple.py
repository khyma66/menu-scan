#!/usr/bin/env python3
"""
Simple pipeline runner that processes each video URL through NoteGPT
and stores transcripts in separate table
"""

import asyncio
import os
import sys
from supabase import create_client
from dotenv import load_dotenv
from youtube_playlist_extractor import YouTubePlaylistExtractor
from notegpt_mcp_server import extract_transcript
from youtube_transcript_extractor import extract_youtube_transcript
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

CHANNEL_URL = "https://www.youtube.com/@srichagantikoteswararaogar4451"

async def process_video_url(youtube_url: str, supabase_client, playlist_id: str = None, playlist_title: str = None):
    """Process a single video URL through NoteGPT and store in database"""
    try:
        logger.info(f"Processing: {youtube_url}")
        
        # Try YouTube direct extraction first (more reliable)
        logger.info("Trying YouTube direct transcript extraction...")
        transcript_result = extract_youtube_transcript(youtube_url)
        
        # If YouTube extraction fails, try NoteGPT
        if not transcript_result.get("success"):
            logger.info("YouTube extraction failed, trying NoteGPT.io...")
            transcript_result = await extract_transcript(youtube_url)
        
        if not transcript_result.get("success"):
            logger.error(f"Failed to extract transcript: {transcript_result.get('error')}")
            return {
                "success": False,
                "youtube_url": youtube_url,
                "error": transcript_result.get("error", "Unknown error")
            }
        
        video_title = transcript_result.get("title", "Untitled")
        transcript_text = transcript_result.get("transcript", "")
        video_id = youtube_url.split("v=")[-1].split("&")[0] if "v=" in youtube_url else ""
        
        logger.info(f"✓ Got transcript for: {video_title}")
        logger.info(f"  Transcript length: {len(transcript_text)} characters")
        
        # Store in database table
        try:
            # Store in playlist_transcripts table
            insert_data = {
                "playlist_id": playlist_id or "single_videos",
                "playlist_title": playlist_title or "Individual Videos",
                "video_id": video_id,
                "youtube_url": youtube_url,
                "title": video_title,
                "transcript": transcript_text[:5000],  # First 5000 chars in DB
                "storage_path": f"videos/{video_id}_{video_title[:50]}.txt",
                "storage_url": f"https://jlfqzcaospvspmzbvbxd.supabase.co/storage/v1/object/public/video-transcripts/videos/{video_id}_{video_title[:50]}.txt",
                "metadata": {
                    "extracted_at": transcript_result.get("extracted_at"),
                    "transcript_length": len(transcript_text)
                },
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = supabase_client.table("playlist_transcripts").insert(insert_data).execute()
            
            logger.info(f"✓ Stored in database: {video_title}")
            
            # Also store full transcript in storage
            try:
                safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
                filename = f"videos/{video_id}_{safe_title}.txt"
                
                supabase_client.storage.from_("video-transcripts").upload(
                    filename,
                    transcript_text.encode('utf-8'),
                    file_options={"content-type": "text/plain", "upsert": "true"}
                )
                
                logger.info(f"✓ Stored in storage: {filename}")
            except Exception as storage_error:
                logger.warning(f"Storage upload failed (continuing): {storage_error}")
            
            return {
                "success": True,
                "youtube_url": youtube_url,
                "title": video_title,
                "transcript_length": len(transcript_text),
                "stored": True
            }
            
        except Exception as db_error:
            logger.error(f"Database error: {db_error}")
            return {
                "success": False,
                "youtube_url": youtube_url,
                "error": str(db_error)
            }
            
    except Exception as e:
        logger.error(f"Error processing {youtube_url}: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "youtube_url": youtube_url,
            "error": str(e)
        }

async def main():
    """Main pipeline runner"""
    supabase_url = os.getenv("SUPABASE_URL", "https://jlfqzcaospvspmzbvbxd.supabase.co")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_key:
        print("Error: SUPABASE_KEY must be set")
        sys.exit(1)
    
    supabase_client = create_client(supabase_url, supabase_key)
    
    print("\n" + "="*60)
    print("VIDEO TRANSCRIPT PIPELINE")
    print("="*60)
    print(f"Channel: {CHANNEL_URL}")
    print(f"Process: Extract URLs → NoteGPT → Store in Database")
    print("="*60 + "\n")
    
    # Extract playlists and videos
    extractor = YouTubePlaylistExtractor()
    
    print("Step 1: Extracting playlists from channel...")
    playlists = extractor.get_channel_playlists(CHANNEL_URL)
    print(f"Found {len(playlists)} playlists\n")
    
    all_results = []
    total_processed = 0
    total_failed = 0
    
    # Process each playlist
    for playlist_idx, playlist in enumerate(playlists, 1):
        print(f"\n{'='*60}")
        print(f"Playlist {playlist_idx}/{len(playlists)}: {playlist['title']}")
        print(f"{'='*60}")
        
        # Get videos from playlist
        videos = extractor.get_playlist_videos(playlist['url'])
        print(f"Found {len(videos)} videos in playlist\n")
        
        # Process each video
        for video_idx, video in enumerate(videos, 1):
            print(f"\n[{video_idx}/{len(videos)}] Processing: {video['title']}")
            print(f"URL: {video['url']}")
            
            result = await process_video_url(
                video['url'],
                supabase_client,
                playlist_id=playlist['playlist_id'],
                playlist_title=playlist['title']
            )
            
            if result.get("success"):
                total_processed += 1
                print(f"✓ Success: {result['title']} ({result['transcript_length']} chars)")
            else:
                total_failed += 1
                print(f"✗ Failed: {result.get('error', 'Unknown error')}")
            
            all_results.append(result)
            
            # Delay between videos
            if video_idx < len(videos):
                await asyncio.sleep(3)
        
        # Update playlist metadata
        try:
            supabase_client.table("playlists").upsert({
                "playlist_id": playlist['playlist_id'],
                "title": playlist['title'],
                "url": playlist['url'],
                "video_count": len(videos),
                "processed_videos": sum(1 for r in all_results if r.get("success")),
                "failed_videos": sum(1 for r in all_results if not r.get("success")),
                "status": "completed"
            }).execute()
        except Exception as e:
            logger.warning(f"Could not update playlist metadata: {e}")
    
    # Final summary
    print("\n" + "="*60)
    print("PIPELINE COMPLETE")
    print("="*60)
    print(f"Total playlists: {len(playlists)}")
    print(f"Total videos processed: {total_processed}")
    print(f"Total videos failed: {total_failed}")
    print("="*60)
    
    # Show failed videos
    if total_failed > 0:
        print("\nFailed videos:")
        for result in all_results:
            if not result.get("success"):
                print(f"  - {result.get('youtube_url', 'Unknown')}: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main())

