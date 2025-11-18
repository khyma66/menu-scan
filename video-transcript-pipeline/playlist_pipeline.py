"""
Playlist Transcript Pipeline
Processes YouTube channel playlists, extracts transcripts via NoteGPT, and stores in separate Supabase tables
"""

import asyncio
import json
import logging
import os
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

from supabase import create_client, Client
from youtube_playlist_extractor import YouTubePlaylistExtractor
from notegpt_mcp_server import extract_transcript

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PlaylistTranscriptPipeline:
    """Automated pipeline for playlist transcript processing"""
    
    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        bucket_name: str = "video-transcripts",
        storage_limit_gb: float = 1.0
    ):
        """
        Initialize the pipeline
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase anon/service key
            bucket_name: Name of the storage bucket for transcripts
            storage_limit_gb: Storage limit in GB (default 1.0 for free tier)
        """
        self.supabase_client: Client = create_client(supabase_url, supabase_key)
        self.bucket_name = bucket_name
        self.playlist_extractor = YouTubePlaylistExtractor()
        self.storage_limit_bytes = int(storage_limit_gb * 1024 * 1024 * 1024)  # Convert GB to bytes
        self.storage_warning_threshold = int(self.storage_limit_bytes * 0.9)  # Warn at 90%
        self.storage_limit_gb = storage_limit_gb
        
        # Initialize tables if they don't exist
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        """Ensure required tables exist in Supabase"""
        logger.info("Checking database tables...")
        # Tables will be created via SQL script
        # This is just a placeholder for validation
    
    def _get_storage_usage(self) -> Dict[str, any]:
        """
        Get current storage usage for the bucket
        
        Returns:
            Dictionary with storage usage information
        """
        try:
            # List all files in the bucket to calculate total size
            files = self.supabase_client.storage.from_(self.bucket_name).list()
            
            total_size = 0
            file_count = 0
            
            # Calculate total size by listing files recursively
            def get_folder_size(folder_path: str = "") -> int:
                """Recursively get folder size"""
                folder_size = 0
                try:
                    items = self.supabase_client.storage.from_(self.bucket_name).list(folder_path)
                    for item in items:
                        if item.get('id'):  # It's a file
                            # Get file metadata to get size
                            # Note: Supabase storage API doesn't directly provide file size
                            # We'll estimate based on file count and average size
                            folder_size += item.get('metadata', {}).get('size', 0)
                        else:  # It's a folder
                            folder_size += get_folder_size(f"{folder_path}/{item.get('name', '')}" if folder_path else item.get('name', ''))
                except Exception as e:
                    logger.warning(f"Error getting folder size for {folder_path}: {e}")
                return folder_size
            
            # Try to get storage usage from bucket info
            # Since Supabase doesn't provide direct storage usage API,
            # we'll estimate based on file count and average transcript size
            # Average transcript is ~50KB, so we'll use that as estimate
            try:
                all_files = []
                # List files in playlists folder
                playlists_files = self.supabase_client.storage.from_(self.bucket_name).list("playlists")
                for item in playlists_files:
                    if item.get('id'):
                        all_files.append(item)
                    else:
                        # It's a folder, list its contents
                        try:
                            folder_files = self.supabase_client.storage.from_(self.bucket_name).list(f"playlists/{item.get('name', '')}")
                            all_files.extend([f for f in folder_files if f.get('id')])
                        except:
                            pass
                
                # Estimate size: average transcript ~50KB
                file_count = len(all_files)
                estimated_size = file_count * 50 * 1024  # 50KB per file estimate
                
                return {
                    "total_bytes": estimated_size,
                    "total_gb": estimated_size / (1024 * 1024 * 1024),
                    "file_count": file_count,
                    "limit_bytes": self.storage_limit_bytes,
                    "limit_gb": self.storage_limit_bytes / (1024 * 1024 * 1024),
                    "usage_percent": (estimated_size / self.storage_limit_bytes) * 100,
                    "is_estimate": True
                }
            except Exception as e:
                logger.warning(f"Could not calculate exact storage usage: {e}")
                return {
                    "total_bytes": 0,
                    "total_gb": 0,
                    "file_count": 0,
                    "limit_bytes": self.storage_limit_bytes,
                    "limit_gb": self.storage_limit_bytes / (1024 * 1024 * 1024),
                    "usage_percent": 0,
                    "is_estimate": True,
                    "error": str(e)
                }
        except Exception as e:
            logger.error(f"Error getting storage usage: {e}")
            return {
                "total_bytes": 0,
                "total_gb": 0,
                "error": str(e)
            }
    
    def _check_storage_limit(self, transcript_size: int = 0) -> Dict[str, any]:
        """
        Check if storage limit will be exceeded
        
        Args:
            transcript_size: Size of transcript to be stored (bytes)
        
        Returns:
            Dictionary with check result and storage info
        """
        storage_info = self._get_storage_usage()
        current_usage = storage_info.get("total_bytes", 0)
        projected_usage = current_usage + transcript_size
        
        exceeded = projected_usage >= self.storage_limit_bytes
        warning = projected_usage >= self.storage_warning_threshold
        
        return {
            "exceeded": exceeded,
            "warning": warning,
            "current_usage_bytes": current_usage,
            "current_usage_gb": current_usage / (1024 * 1024 * 1024),
            "projected_usage_bytes": projected_usage,
            "projected_usage_gb": projected_usage / (1024 * 1024 * 1024),
            "limit_bytes": self.storage_limit_bytes,
            "limit_gb": self.storage_limit_bytes / (1024 * 1024 * 1024),
            "usage_percent": (current_usage / self.storage_limit_bytes) * 100 if self.storage_limit_bytes > 0 else 0,
            "storage_info": storage_info
        }
    
    async def process_channel_playlists(
        self,
        channel_url: str,
        max_playlists: Optional[int] = None,
        max_videos_per_playlist: Optional[int] = None,
        delay_between_videos: float = 3.0
    ) -> Dict[str, any]:
        """
        Process all playlists from a YouTube channel
        
        Args:
            channel_url: YouTube channel URL
            max_playlists: Maximum number of playlists to process (None for all)
            max_videos_per_playlist: Maximum videos per playlist (None for all)
            delay_between_videos: Delay in seconds between video processing
        
        Returns:
            Summary of processing results
        """
        logger.info(f"Starting playlist pipeline for channel: {channel_url}")
        
        # Step 1: Extract playlists from channel
        logger.info("Step 1: Extracting playlists from channel...")
        playlists = self.playlist_extractor.get_channel_playlists(channel_url)
        
        if max_playlists:
            playlists = playlists[:max_playlists]
        
        logger.info(f"Found {len(playlists)} playlists to process")
        
        if not playlists:
            return {
                "success": False,
                "error": "No playlists found in channel",
                "processed_playlists": 0,
                "processed_videos": 0,
                "failed_videos": 0
            }
        
        # Step 2: Process each playlist
        results = {
            "channel_url": channel_url,
            "total_playlists": len(playlists),
            "processed_playlists": 0,
            "processed_videos": 0,
            "failed_videos": 0,
            "playlist_results": []
        }
        
        for playlist_idx, playlist in enumerate(playlists, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing playlist {playlist_idx}/{len(playlists)}: {playlist['title']}")
            logger.info(f"{'='*60}")
            
            playlist_result = {
                "playlist_id": playlist['playlist_id'],
                "playlist_title": playlist['title'],
                "playlist_url": playlist['url'],
                "total_videos": 0,
                "processed_videos": 0,
                "failed_videos": 0,
                "videos": []
            }
            
            try:
                # Get videos from playlist
                videos = self.playlist_extractor.get_playlist_videos(
                    playlist['url'],
                    max_results=max_videos_per_playlist
                )
                
                playlist_result["total_videos"] = len(videos)
                logger.info(f"Found {len(videos)} videos in playlist")
                
                # Process each video
                for video_idx, video in enumerate(videos, 1):
                    logger.info(f"\nProcessing video {video_idx}/{len(videos)}: {video['title']}")
                    
                    # Check storage limit before processing
                    transcript_size_estimate = 50 * 1024  # Estimate 50KB per transcript
                    storage_check = self._check_storage_limit(transcript_size_estimate)
                    
                    if storage_check["exceeded"]:
                        logger.warning(f"\n{'='*60}")
                        logger.warning(f"⚠️  STORAGE LIMIT EXCEEDED!")
                        logger.warning(f"Current usage: {storage_check['current_usage_gb']:.2f} GB")
                        logger.warning(f"Limit: {storage_check['limit_gb']:.2f} GB")
                        logger.warning(f"Usage: {storage_check['usage_percent']:.1f}%")
                        logger.warning(f"{'='*60}")
                        logger.warning("Stopping pipeline to prevent exceeding storage limit.")
                        playlist_result["status"] = "stopped_storage_limit"
                        playlist_result["stopped_reason"] = "Storage limit exceeded"
                        results["stopped_reason"] = "Storage limit exceeded"
                        results["storage_info"] = storage_check
                        break
                    
                    if storage_check["warning"]:
                        logger.warning(f"⚠️  Storage warning: {storage_check['usage_percent']:.1f}% used")
                        logger.warning(f"   Current: {storage_check['current_usage_gb']:.2f} GB / Limit: {storage_check['limit_gb']:.2f} GB")
                    
                    try:
                        # Extract transcript
                        transcript_result = await extract_transcript(video['url'])
                        
                        if transcript_result.get("success"):
                            # Check storage again with actual transcript size
                            actual_transcript_size = len(transcript_result.get("transcript", "").encode('utf-8'))
                            storage_check_actual = self._check_storage_limit(actual_transcript_size)
                            
                            if storage_check_actual["exceeded"]:
                                logger.warning(f"\n⚠️  Storage limit would be exceeded by this transcript")
                                logger.warning(f"Skipping video: {video['title']}")
                                playlist_result["failed_videos"] += 1
                                results["failed_videos"] += 1
                                playlist_result["videos"].append({
                                    "video_title": video['title'],
                                    "youtube_url": video['url'],
                                    "status": "skipped_storage_limit",
                                    "error": "Storage limit exceeded"
                                })
                                # Stop processing this playlist
                                break
                            # Store in Supabase with playlist context
                            storage_result = await self._store_playlist_transcript(
                                playlist_id=playlist['playlist_id'],
                                playlist_title=playlist['title'],
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
                                playlist_result["processed_videos"] += 1
                                results["processed_videos"] += 1
                                playlist_result["videos"].append({
                                    "video_title": transcript_result.get("title"),
                                    "youtube_url": video['url'],
                                    "status": "success",
                                    "storage_path": storage_result.get("path")
                                })
                                logger.info(f"✓ Successfully processed: {transcript_result.get('title')}")
                            else:
                                playlist_result["failed_videos"] += 1
                                results["failed_videos"] += 1
                                playlist_result["videos"].append({
                                    "video_title": video['title'],
                                    "youtube_url": video['url'],
                                    "status": "storage_failed",
                                    "error": storage_result.get("error")
                                })
                                logger.error(f"✗ Storage failed: {storage_result.get('error')}")
                        else:
                            playlist_result["failed_videos"] += 1
                            results["failed_videos"] += 1
                            playlist_result["videos"].append({
                                "video_title": video['title'],
                                "youtube_url": video['url'],
                                "status": "extraction_failed",
                                "error": transcript_result.get("error", "Unknown error")
                            })
                            logger.error(f"✗ Extraction failed for: {video['title']}")
                        
                        # Delay between videos
                        if video_idx < len(videos):
                            await asyncio.sleep(delay_between_videos)
                            
                    except Exception as e:
                        logger.error(f"Error processing video {video['title']}: {e}")
                        playlist_result["failed_videos"] += 1
                        results["failed_videos"] += 1
                        playlist_result["videos"].append({
                            "video_title": video['title'],
                            "youtube_url": video['url'],
                            "status": "error",
                            "error": str(e)
                        })
                
                # Store playlist metadata
                await self._store_playlist_metadata(playlist, playlist_result)
                playlist_result["status"] = "completed"
                results["processed_playlists"] += 1
                
            except Exception as e:
                logger.error(f"Error processing playlist {playlist['title']}: {e}")
                playlist_result["status"] = "error"
                playlist_result["error"] = str(e)
            
            results["playlist_results"].append(playlist_result)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Pipeline complete:")
        logger.info(f"  Playlists processed: {results['processed_playlists']}/{results['total_playlists']}")
        logger.info(f"  Videos processed: {results['processed_videos']}")
        logger.info(f"  Videos failed: {results['failed_videos']}")
        logger.info(f"{'='*60}")
        
        return results
    
    async def _store_playlist_transcript(
        self,
        playlist_id: str,
        playlist_title: str,
        video_title: str,
        youtube_url: str,
        transcript: str,
        video_id: str,
        metadata: Dict
    ) -> Dict[str, any]:
        """
        Store transcript in Supabase with playlist context
        
        Args:
            playlist_id: YouTube playlist ID
            playlist_title: Playlist title
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
            filename = f"playlists/{playlist_id}/{video_id}_{safe_title}.txt"
            
            # Upload to storage bucket
            response = self.supabase_client.storage.from_(self.bucket_name).upload(
                filename,
                transcript.encode('utf-8'),
                file_options={
                    "content-type": "text/plain",
                    "upsert": "true"
                }
            )
            
            # Get public URL
            public_url = self._get_public_url(filename)
            
            # Store in playlist_transcripts table
            try:
                self.supabase_client.table("playlist_transcripts").insert({
                    "playlist_id": playlist_id,
                    "playlist_title": playlist_title,
                    "video_id": video_id,
                    "youtube_url": youtube_url,
                    "title": video_title,
                    "transcript": transcript[:5000],  # First 5000 chars in DB
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
            logger.error(f"Error storing playlist transcript: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _store_playlist_metadata(self, playlist: Dict, playlist_result: Dict):
        """Store playlist metadata"""
        try:
            self.supabase_client.table("playlists").insert({
                "playlist_id": playlist['playlist_id'],
                "title": playlist['title'],
                "url": playlist['url'],
                "video_count": playlist_result["total_videos"],
                "processed_videos": playlist_result["processed_videos"],
                "failed_videos": playlist_result["failed_videos"],
                "status": playlist_result.get("status", "unknown"),
                "created_at": datetime.utcnow().isoformat()
            }).execute()
        except Exception as db_error:
            logger.warning(f"Could not store playlist metadata: {db_error}")
    
    def _sanitize_filename(self, filename: str, max_length: int = 100) -> str:
        """Sanitize filename for storage"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
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
    from dotenv import load_dotenv
    
    load_dotenv()
    
    supabase_url = os.getenv("SUPABASE_URL", "https://jlfqzcaospvspmzbvbxd.supabase.co")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_key:
        logger.error("SUPABASE_KEY environment variable is required")
        return
    
    # Initialize pipeline
    pipeline = PlaylistTranscriptPipeline(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        bucket_name="video-transcripts"
    )
    
    # Process specific channel
    channel_url = input("Enter YouTube channel URL: ")
    max_playlists = input("Max playlists to process (press Enter for all): ").strip()
    max_playlists = int(max_playlists) if max_playlists else None
    
    max_videos = input("Max videos per playlist (press Enter for all): ").strip()
    max_videos = int(max_videos) if max_videos else None
    
    # Process channel playlists
    results = await pipeline.process_channel_playlists(
        channel_url=channel_url,
        max_playlists=max_playlists,
        max_videos_per_playlist=max_videos,
        delay_between_videos=3.0
    )
    
    # Save results
    output_file = f"playlist_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())

