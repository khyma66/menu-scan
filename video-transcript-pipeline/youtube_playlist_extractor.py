"""
YouTube Playlist Extractor
Extracts all video URLs from YouTube playlists
"""

import asyncio
import re
import logging
from typing import List, Dict, Optional
from yt_dlp import YoutubeDL
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class YouTubePlaylistExtractor:
    """Extract video URLs from YouTube playlists"""
    
    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'skip_download': True,
        }
    
    def get_playlist_videos(self, playlist_url: str, max_results: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Get all video URLs from a YouTube playlist
        
        Args:
            playlist_url: YouTube playlist URL
            max_results: Maximum number of videos to retrieve (None for all)
        
        Returns:
            List of dictionaries with video information
        """
        try:
            ydl_opts = {
                **self.ydl_opts,
                'extract_flat': True,
                'playlistend': max_results if max_results else None,
            }
            
            videos = []
            
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(playlist_url, download=False)
                
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
                                'playlist_id': info.get('id', ''),
                                'playlist_title': info.get('title', ''),
                            })
            
            logger.info(f"Extracted {len(videos)} videos from playlist")
            return videos
            
        except Exception as e:
            logger.error(f"Error extracting playlist videos: {e}")
            raise
    
    def get_channel_playlists(self, channel_url: str) -> List[Dict[str, str]]:
        """
        Get all playlists from a YouTube channel
        
        Args:
            channel_url: YouTube channel URL
        
        Returns:
            List of playlist information
        """
        try:
            # Get channel playlists URL
            if '/@' in channel_url:
                channel_handle = channel_url.split('/@')[-1].split('/')[0]
                playlists_url = f"https://www.youtube.com/@{channel_handle}/playlists"
            elif '/channel/' in channel_url:
                channel_id = channel_url.split('/channel/')[-1].split('/')[0]
                playlists_url = f"https://www.youtube.com/channel/{channel_id}/playlists"
            else:
                playlists_url = f"{channel_url}/playlists"
            
            ydl_opts = {
                **self.ydl_opts,
                'extract_flat': True,
            }
            
            playlists = []
            
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(playlists_url, download=False)
                
                if 'entries' in info:
                    for entry in info['entries']:
                        if entry:
                            playlist_id = entry.get('id', '')
                            playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
                            playlists.append({
                                'playlist_id': playlist_id,
                                'title': entry.get('title', 'Untitled'),
                                'url': playlist_url,
                                'video_count': entry.get('playlist_count', 0),
                            })
            
            logger.info(f"Found {len(playlists)} playlists in channel")
            return playlists
            
        except Exception as e:
            logger.error(f"Error extracting channel playlists: {e}")
            raise


async def main():
    """Test the extractor"""
    extractor = YouTubePlaylistExtractor()
    
    # Example: Get playlists from channel
    channel_url = input("Enter YouTube channel URL: ")
    
    print(f"\nExtracting playlists from: {channel_url}")
    playlists = extractor.get_channel_playlists(channel_url)
    
    print(f"\nFound {len(playlists)} playlists:")
    for i, playlist in enumerate(playlists, 1):
        print(f"{i}. {playlist['title']} ({playlist['video_count']} videos)")
        print(f"   URL: {playlist['url']}\n")
    
    # Get videos from first playlist
    if playlists:
        playlist_url = playlists[0]['url']
        print(f"\nExtracting videos from playlist: {playlists[0]['title']}")
        videos = extractor.get_playlist_videos(playlist_url, max_results=10)
        
        print(f"\nFound {len(videos)} videos:")
        for i, video in enumerate(videos, 1):
            print(f"{i}. {video['title']}")
            print(f"   URL: {video['url']}\n")


if __name__ == "__main__":
    asyncio.run(main())

