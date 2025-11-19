"""
Alternative: Extract transcripts directly from YouTube using yt-dlp
This is more reliable than browser automation
"""

import logging
from typing import Dict, Any, Optional
from yt_dlp import YoutubeDL
import time

logger = logging.getLogger(__name__)

def extract_youtube_transcript(youtube_url: str) -> Dict[str, Any]:
    """
    Extract transcript directly from YouTube using yt-dlp
    This is more reliable than browser automation
    """
    try:
        ydl_opts = {
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en', 'en-US', 'en-GB'],  # Prefer English
            'skip_download': True,
            'quiet': True,
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            
            video_id = info.get('id', '')
            video_title = info.get('title', 'Untitled')
            
            # Try to get subtitles/transcript
            subtitles = info.get('subtitles', {})
            automatic_captions = info.get('automatic_captions', {})
            
            transcript_text = ""
            
            # Try to get English subtitles first
            for lang in ['en', 'en-US', 'en-GB', 'en-IN']:
                # Try manual subtitles first
                if lang in subtitles and subtitles[lang]:
                    subtitle_entry = subtitles[lang][0] if isinstance(subtitles[lang], list) else subtitles[lang]
                    subtitle_url = subtitle_entry.get('url', '')
                    if subtitle_url:
                        try:
                            import urllib.request
                            subtitle_data = urllib.request.urlopen(subtitle_url).read().decode('utf-8')
                            # Parse and extract text
                            transcript_text = parse_subtitle_format(subtitle_data)
                            if transcript_text and len(transcript_text) > 50:
                                break
                        except Exception as e:
                            logger.warning(f"Error fetching subtitle {lang}: {e}")
                            continue
                
                # Try automatic captions
                if lang in automatic_captions and automatic_captions[lang]:
                    caption_entry = automatic_captions[lang][0] if isinstance(automatic_captions[lang], list) else automatic_captions[lang]
                    caption_url = caption_entry.get('url', '')
                    if caption_url:
                        try:
                            import urllib.request
                            caption_data = urllib.request.urlopen(caption_url).read().decode('utf-8')
                            transcript_text = parse_subtitle_format(caption_data)
                            if transcript_text and len(transcript_text) > 50:
                                break
                        except Exception as e:
                            logger.warning(f"Error fetching caption {lang}: {e}")
                            continue
            
            if not transcript_text:
                # Try to get description as fallback
                transcript_text = info.get('description', '')
                if len(transcript_text) < 100:
                    return {
                        "success": False,
                        "youtube_url": youtube_url,
                        "error": "No transcript available for this video"
                    }
            
            return {
                "success": True,
                "youtube_url": youtube_url,
                "title": video_title,
                "transcript": transcript_text.strip(),
                "extracted_at": time.time(),
                "method": "youtube_direct"
            }
            
    except Exception as e:
        logger.error(f"Error extracting YouTube transcript: {e}")
        return {
            "success": False,
            "youtube_url": youtube_url,
            "error": str(e)
        }

def parse_subtitle_format(subtitle_data: str) -> str:
    """Parse SRT, VTT, or JSON subtitle format and extract text"""
    import re
    import json
    
    # Try parsing as JSON first (YouTube sometimes returns JSON)
    try:
        subtitle_json = json.loads(subtitle_data)
        if 'events' in subtitle_json:
            # Extract text from JSON events
            text_parts = []
            for event in subtitle_json.get('events', []):
                for seg in event.get('segs', []):
                    text = seg.get('utf8', '').strip()
                    if text:
                        text_parts.append(text)
            return ' '.join(text_parts)
    except (json.JSONDecodeError, KeyError):
        pass
    
    # Parse SRT/VTT format
    # Remove timestamps like 00:00:00,000 --> 00:00:05,000
    subtitle_data = re.sub(r'\d{2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,.]\d{3}', '', subtitle_data)
    # Remove sequence numbers
    subtitle_data = re.sub(r'^\d+$', '', subtitle_data, flags=re.MULTILINE)
    # Remove HTML tags
    subtitle_data = re.sub(r'<[^>]+>', '', subtitle_data)
    # Remove WEBVTT header
    subtitle_data = re.sub(r'WEBVTT\s*', '', subtitle_data)
    # Clean up whitespace
    lines = [line.strip() for line in subtitle_data.split('\n') if line.strip()]
    # Remove empty lines and timestamp lines
    text_lines = [line for line in lines if not re.match(r'^\d+$', line) and not re.match(r'^\d{2}:', line)]
    
    return ' '.join(text_lines)

