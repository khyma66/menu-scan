"""
Automated Video Transcript Pipeline
Processes YouTube channel videos, extracts transcripts via NoteGPT, and stores in Supabase
"""

import asyncio
import json
import logging
import os
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

from supabase import create_client, Client
from youtube_channel_extractor import YouTubeChannelExtractor
from notegpt_mcp_server import extract_transcript

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TranscriptPipeline:
    """Automated pipeline for video transcript processing"""
    
    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        bucket_name: str = "video-transcripts"
    ):
        """
        Initialize the pipeline
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase anon/service key
            bucket_name: Name of the storage bucket for transcripts
        """
        self.supabase_client: Client = create_client(supabase_url, supabase_key)
        self.bucket_name = bucket_name
        self.channel_extractor = YouTubeChannelExtractor()
        
        # Initialize bucket if it doesn't exist
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure the transcript bucket exists in Supabase"""
        try:
            # Try to get bucket info
            buckets = self.supabase_client.storage.list_buckets()
            bucket_names = [b.name for b in buckets]
            
            if self.bucket_name not in bucket_names:
                logger.info(f"Creating bucket: {self.bucket_name}")
                # Note: Bucket creation requires service role key
                # For free tier, you may need to create it manually in Supabase dashboard
                logger.warning(
                    f"Bucket '{self.bucket_name}' not found. "
                    f"Please create it manually in Supabase dashboard for free tier."
                )
            else:
                logger.info(f"Bucket '{self.bucket_name}' exists")
                
        except Exception as e:
            logger.error(f"Error checking bucket: {e}")
            logger.warning("Continuing anyway - bucket may need manual creation")
    
    async def process_channel(
        self,
        channel_url: str,
        max_videos: Optional[int] = None,
        delay_between_videos: float = 3.0
    ) -> Dict[str, any]:
        """
        Process all videos from a YouTube channel
        
        Args:
            channel_url: YouTube channel URL
            max_videos: Maximum number of videos to process (None for all)
            delay_between_videos: Delay in seconds between video processing
        
        Returns:
            Summary of processing results
        """
        logger.info(f"Starting pipeline for channel: {channel_url}")
        
        # Step 1: Extract video URLs from channel
        logger.info("Step 1: Extracting video URLs from channel...")
        videos = self.channel_extractor.get_channel_videos(channel_url, max_results=max_videos)
        logger.info(f"Found {len(videos)} videos to process")
        
        if not videos:
            return {
                "success": False,
                "error": "No videos found in channel",
                "processed": 0,
                "failed": 0
            }
        
        # Step 2: Process each video
        results = {
            "channel_url": channel_url,
            "total_videos": len(videos),
            "processed": 0,
            "failed": 0,
            "results": []
        }
        
        for i, video in enumerate(videos, 1):
            logger.info(f"\nProcessing video {i}/{len(videos)}: {video['title']}")
            
            try:
                # Extract transcript
                transcript_result = await extract_transcript(video['url'])
                
                if transcript_result.get("success"):
                    # Store in Supabase
                    storage_result = await self._store_transcript(
                        video_title=transcript_result.get("title", video['title']),
                        youtube_url=video['url'],
                        transcript=transcript_result.get("transcript", ""),
                        video_id=video.get('video_id', ''),
                        metadata={
                            "duration": video.get('duration', 0),
                            "view_count": video.get('view_count', 0),
                            "extracted_at": transcript_result.get("extracted_at"),
                        }
                    )
                    
                    if storage_result["success"]:
                        results["processed"] += 1
                        results["results"].append({
                            "video_title": transcript_result.get("title"),
                            "youtube_url": video['url'],
                            "status": "success",
                            "storage_path": storage_result.get("path")
                        })
                        logger.info(f"✓ Successfully processed: {transcript_result.get('title')}")
                    else:
                        results["failed"] += 1
                        results["results"].append({
                            "video_title": video['title'],
                            "youtube_url": video['url'],
                            "status": "storage_failed",
                            "error": storage_result.get("error")
                        })
                        logger.error(f"✗ Storage failed: {storage_result.get('error')}")
                else:
                    results["failed"] += 1
                    results["results"].append({
                        "video_title": video['title'],
                        "youtube_url": video['url'],
                        "status": "extraction_failed",
                        "error": transcript_result.get("error", "Unknown error")
                    })
                    logger.error(f"✗ Extraction failed for: {video['title']}")
                
                # Delay between videos to avoid rate limiting
                if i < len(videos):
                    await asyncio.sleep(delay_between_videos)
                    
            except Exception as e:
                logger.error(f"Error processing video {video['title']}: {e}")
                results["failed"] += 1
                results["results"].append({
                    "video_title": video['title'],
                    "youtube_url": video['url'],
                    "status": "error",
                    "error": str(e)
                })
        
        logger.info(f"\nPipeline complete: {results['processed']} processed, {results['failed']} failed")
        return results
    
    async def _store_transcript(
        self,
        video_title: str,
        youtube_url: str,
        transcript: str,
        video_id: str,
        metadata: Dict
    ) -> Dict[str, any]:
        """
        Store transcript in Supabase storage
        
        Args:
            video_title: Video title
            youtube_url: YouTube URL
            transcript: Transcript text
            video_id: YouTube video ID
            metadata: Additional metadata
        
        Returns:
            Result dictionary with success status and path
        """
        try:
            # Sanitize filename
            safe_title = self._sanitize_filename(video_title)
            filename = f"{video_id}_{safe_title}.txt"
            
            # Upload to storage bucket
            response = self.supabase_client.storage.from_(self.bucket_name).upload(
                filename,
                transcript.encode('utf-8'),
                file_options={
                    "content-type": "text/plain",
                    "upsert": "true"  # Overwrite if exists
                }
            )
            
            # Get public URL
            public_url = self._get_public_url(filename)
            
            # Also store metadata in database table (if exists)
            try:
                self.supabase_client.table("video_transcripts").insert({
                    "video_id": video_id,
                    "youtube_url": youtube_url,
                    "title": video_title,
                    "transcript": transcript[:5000],  # Store first 5000 chars in DB
                    "storage_path": filename,
                    "storage_url": public_url,
                    "metadata": metadata,
                    "created_at": datetime.utcnow().isoformat()
                }).execute()
            except Exception as db_error:
                logger.warning(f"Could not store in database table (may not exist): {db_error}")
            
            return {
                "success": True,
                "path": filename,
                "url": public_url
            }
            
        except Exception as e:
            logger.error(f"Error storing transcript: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _sanitize_filename(self, filename: str, max_length: int = 100) -> str:
        """Sanitize filename for storage"""
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > max_length:
            filename = filename[:max_length]
        
        return filename.strip()
    
    def _get_public_url(self, filename: str) -> str:
        """Get public URL for stored file"""
        supabase_url = os.getenv("SUPABASE_URL", "")
        return f"{supabase_url}/storage/v1/object/public/{self.bucket_name}/{filename}"


async def main():
    """Main entry point"""
    import os
    
    # Get configuration from environment
    supabase_url = os.getenv("SUPABASE_URL", "https://jlfqzcaospvspmzbvbxd.supabase.co")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_key:
        logger.error("SUPABASE_KEY environment variable is required")
        return
    
    # Initialize pipeline
    pipeline = TranscriptPipeline(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        bucket_name="video-transcripts"
    )
    
    # Get channel URL from user
    channel_url = input("Enter YouTube channel URL: ")
    max_videos = input("Max videos to process (press Enter for all): ").strip()
    max_videos = int(max_videos) if max_videos else None
    
    # Process channel
    results = await pipeline.process_channel(
        channel_url=channel_url,
        max_videos=max_videos,
        delay_between_videos=3.0
    )
    
    # Save results
    output_file = f"pipeline_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\nResults saved to: {output_file}")
    
    # Close browser
    await pipeline.notegpt_server.close()


if __name__ == "__main__":
    asyncio.run(main())

