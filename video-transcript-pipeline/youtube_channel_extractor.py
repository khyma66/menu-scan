"""
YouTube Channel URL Extractor
Extracts all video URLs from a YouTube channel
"""

import asyncio
import re
import logging
from typing import List, Dict, Optional
from urllib.parse import urlparse, parse_qs
import httpx
from yt_dlp import YoutubeDL
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class YouTubeChannelExtractor:
    """Extract video URLs from YouTube channels"""
    
    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'skip_download': True,
        }
    
    def extract_channel_id(self, channel_url: str) -> Optional[str]:
        """Extract channel ID from various YouTube URL formats"""
        # Handle different URL formats:
        # https://www.youtube.com/channel/UC...
        # https://www.youtube.com/@channelname
        # https://www.youtube.com/c/channelname
        # https://youtube.com/user/username
        
        patterns = [
            r'youtube\.com/channel/([a-zA-Z0-9_-]+)',
            r'youtube\.com/@([a-zA-Z0-9_-]+)',
            r'youtube\.com/c/([a-zA-Z0-9_-]+)',
            r'youtube\.com/user/([a-zA-Z0-9_-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, channel_url)
            if match:
                return match.group(1)
        
        return None
    
    def get_channel_videos(self, channel_url: str, max_results: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Get all video URLs from a YouTube channel
        
        Args:
            channel_url: YouTube channel URL
            max_results: Maximum number of videos to retrieve (None for all)
        
        Returns:
            List of dictionaries with 'url' and 'title' keys
        """
        try:
            # Configure yt-dlp options
            ydl_opts = {
                **self.ydl_opts,
                'extract_flat': True,
                'playlistend': max_results if max_results else None,
            }
            
            videos = []
            
            with YoutubeDL(ydl_opts) as ydl:
                # Extract channel info and videos
                info = ydl.extract_info(channel_url, download=False)
                
                if 'entries' in info:
                    for entry in info['entries']:
                        if entry:
                            video_url = f"https://www.youtube.com/watch?v={entry.get('id', '')}"
                            video_title = entry.get('title', 'Untitled')
                            videos.append({
                                'url': video_url,
                                'title': video_title,
                                'video_id': entry.get('id', ''),
                                'duration': entry.get('duration', 0),
                                'view_count': entry.get('view_count', 0),
                            })
            
            logger.info(f"Extracted {len(videos)} videos from channel")
            return videos
            
        except Exception as e:
            logger.error(f"Error extracting channel videos: {e}")
            raise
    
    def get_channel_info(self, channel_url: str) -> Dict[str, any]:
        """Get channel information"""
        try:
            ydl_opts = {
                **self.ydl_opts,
                'extract_flat': False,
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(channel_url, download=False)
                
                return {
                    'channel_id': info.get('channel_id', ''),
                    'channel_name': info.get('channel', ''),
                    'channel_url': info.get('channel_url', ''),
                    'subscriber_count': info.get('channel_follower_count', 0),
                    'video_count': info.get('playlist_count', 0),
                }
        except Exception as e:
            logger.error(f"Error getting channel info: {e}")
            return {}


async def main():
    """Test the extractor"""
    extractor = YouTubeChannelExtractor()
    
    # Example usage
    channel_url = input("Enter YouTube channel URL: ")
    
    print(f"\nExtracting videos from: {channel_url}")
    videos = extractor.get_channel_videos(channel_url, max_results=10)
    
    print(f"\nFound {len(videos)} videos:")
    for i, video in enumerate(videos, 1):
        print(f"{i}. {video['title']}")
        print(f"   URL: {video['url']}\n")
    
    # Save to JSON
    with open('channel_videos.json', 'w') as f:
        json.dump(videos, f, indent=2)
    
    print(f"\nSaved {len(videos)} videos to channel_videos.json")


if __name__ == "__main__":
    asyncio.run(main())

