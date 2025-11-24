"""
Telugu Video Auto Transcription Pipeline
Uses Whisper ASR + LLM enhancement for Telugu video transcription
"""

import asyncio
import os
import sys
import subprocess
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import tempfile
import json

from supabase import create_client, Client
from youtube_playlist_extractor import YouTubePlaylistExtractor
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()


class TeluguTranscriptionPipeline:
    """Pipeline for Telugu video transcription using Whisper + LLM"""
    
    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        bucket_name: str = "video-transcripts",
        whisper_model: str = "large-v3",
        language: str = "te"  # Telugu language code
    ):
        """
        Initialize the pipeline
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
            bucket_name: Storage bucket name
            whisper_model: Whisper model size (tiny, base, small, medium, large)
            language: Language code (te for Telugu)
        """
        self.supabase_client: Client = create_client(supabase_url, supabase_key)
        self.bucket_name = bucket_name
        self.whisper_model = whisper_model
        self.language = language
        self.playlist_extractor = YouTubePlaylistExtractor()
        
        # Check if Whisper is installed
        self._check_whisper_installation()
    
    def _check_whisper_installation(self):
        """Check if Whisper and FFmpeg are installed"""
        try:
            # Check FFmpeg
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
            if result.returncode != 0:
                logger.warning("FFmpeg not found. Install with: brew install ffmpeg")
            else:
                logger.info("✓ FFmpeg found")
        except FileNotFoundError:
            logger.error("FFmpeg not installed. Install with: brew install ffmpeg")
        
        try:
            # Check Whisper
            import whisper
            logger.info("✓ Whisper library found")
        except ImportError:
            logger.error("Whisper not installed. Install with: pip install openai-whisper")
    
    def download_video_audio(self, youtube_url: str, output_path: str) -> bool:
        """
        Download video and extract audio using yt-dlp and FFmpeg
        
        Args:
            youtube_url: YouTube video URL
            output_path: Path to save audio file (without extension)
        
        Returns:
            True if successful
        """
        try:
            logger.info(f"Downloading audio from: {youtube_url}")
            
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # Use yt-dlp to download audio directly
            # yt-dlp will add .wav extension automatically
            cmd = [
                'yt-dlp',
                '-x',  # Extract audio
                '--audio-format', 'wav',  # Convert to WAV
                '--audio-quality', '0',  # Best quality
                '-o', f'{output_path}.%(ext)s',  # Output file template
                youtube_url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                # Check if file was created (yt-dlp might add .wav extension)
                if os.path.exists(output_path):
                    logger.info(f"✓ Audio extracted to: {output_path}")
                    return True
                elif os.path.exists(f"{output_path}.wav"):
                    # Rename to expected path
                    os.rename(f"{output_path}.wav", output_path)
                    logger.info(f"✓ Audio extracted to: {output_path}")
                    return True
                else:
                    logger.error(f"Audio file not found at expected path: {output_path}")
                    logger.error(f"yt-dlp output: {result.stdout}")
                    return False
            else:
                logger.error(f"Error downloading audio: {result.stderr}")
                logger.error(f"yt-dlp stdout: {result.stdout}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Download timeout")
            return False
        except Exception as e:
            logger.error(f"Error downloading audio: {e}")
            return False
    
    def transcribe_with_whisper(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe audio using Whisper ASR
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Dictionary with transcription results
        """
        try:
            import whisper
            
            logger.info(f"Loading Whisper model: {self.whisper_model}")
            model = whisper.load_model(self.whisper_model)
            
            logger.info(f"Transcribing audio: {audio_path}")
            logger.info(f"Language: Telugu ({self.language})")
            
            # Transcribe with language specified and Telugu-specific options
            # Force Telugu language and use proper Telugu prompt
            telugu_prompt = "ఇది తెలుగు భాషలో వీడియో. ఇది ధార్మిక లేదా ఆధ్యాత్మిక విషయాలపై చర్చ. తెలుగు అక్షరాలలో వ్రాయండి."
            
            result = model.transcribe(
                audio_path,
                language="te",  # Force Telugu language code
                task="transcribe",
                verbose=True,
                initial_prompt=telugu_prompt,  # Telugu prompt to guide transcription
                condition_on_previous_text=False,  # Disable to avoid script confusion
                compression_ratio_threshold=2.4,
                logprob_threshold=-1.0,
                no_speech_threshold=0.6,
                fp16=False  # Use FP32 for better accuracy
            )
            
            # Extract text and segments
            transcript_text = result.get("text", "").strip()
            segments = result.get("segments", [])
            
            # Verify Telugu script in output
            telugu_chars = sum(1 for c in transcript_text if 0x0C00 <= ord(c) <= 0x0C7F)
            total_chars = len([c for c in transcript_text if c.isalnum()])
            
            if total_chars > 0:
                telugu_ratio = telugu_chars / total_chars
                if telugu_ratio < 0.3:  # Less than 30% Telugu characters
                    logger.warning(f"⚠️ Low Telugu script ratio: {telugu_ratio:.1%}")
                    logger.warning(f"   Transcript may be in wrong script. Sample: {transcript_text[:100]}")
                else:
                    logger.info(f"✓ Telugu script verified: {telugu_ratio:.1%} Telugu characters")
            
            logger.info(f"✓ Transcription complete: {len(transcript_text)} characters")
            
            return {
                "success": True,
                "transcript": transcript_text,
                "segments": segments,
                "language": result.get("language", self.language),
                "duration": result.get("duration", 0)
            }
            
        except ImportError:
            logger.error("Whisper not installed. Install with: pip install openai-whisper")
            return {
                "success": False,
                "error": "Whisper not installed"
            }
        except Exception as e:
            logger.error(f"Error transcribing with Whisper: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def enhance_with_llm(self, raw_transcript: str, video_title: str) -> Dict[str, Any]:
        """
        Enhance transcript using LLM for punctuation, capitalization, and corrections
        
        Args:
            raw_transcript: Raw transcript from Whisper
            video_title: Video title for context
        
        Returns:
            Enhanced transcript
        """
        try:
            # Try to use OpenAI or Anthropic API if available
            openai_key = os.getenv("OPENAI_API_KEY")
            anthropic_key = os.getenv("ANTHROPIC_API_KEY")
            
            if not openai_key and not anthropic_key:
                logger.warning("No LLM API key found, skipping enhancement")
                return {
                    "success": True,
                    "enhanced_transcript": raw_transcript,
                    "enhanced": False
                }
            
            # Use OpenAI if available
            if openai_key:
                try:
                    import openai
                    client = openai.OpenAI(api_key=openai_key)
                    
                    prompt = f"""You are a Telugu language expert. Please enhance this raw transcript from a video titled "{video_title}".

Add proper punctuation, capitalization, and correct any misheard words using context. Keep the Telugu text as-is, only improve formatting and fix obvious errors.

Raw transcript:
{raw_transcript}

Enhanced transcript:"""
                    
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are a Telugu language transcription expert."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3
                    )
                    
                    enhanced = response.choices[0].message.content.strip()
                    
                    logger.info("✓ Transcript enhanced with LLM")
                    
                    return {
                        "success": True,
                        "enhanced_transcript": enhanced,
                        "enhanced": True,
                        "original_length": len(raw_transcript),
                        "enhanced_length": len(enhanced)
                    }
                except Exception as e:
                    logger.warning(f"OpenAI enhancement failed: {e}")
            
            # Fallback: return raw transcript
            return {
                "success": True,
                "enhanced_transcript": raw_transcript,
                "enhanced": False
            }
            
        except Exception as e:
            logger.error(f"Error enhancing transcript: {e}")
            return {
                "success": True,
                "enhanced_transcript": raw_transcript,
                "enhanced": False,
                "error": str(e)
            }
    
    def generate_subtitle_file(self, segments: List[Dict], output_path: str, format: str = "srt") -> bool:
        """
        Generate subtitle file (SRT or VTT) from segments
        
        Args:
            segments: List of transcript segments with timestamps
            output_path: Output file path
            format: Subtitle format (srt or vtt)
        
        Returns:
            True if successful
        """
        try:
            if format == "srt":
                content = self._generate_srt(segments)
            elif format == "vtt":
                content = self._generate_vtt(segments)
            else:
                logger.error(f"Unsupported format: {format}")
                return False
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"✓ Subtitle file generated: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating subtitle file: {e}")
            return False
    
    def _generate_srt(self, segments: List[Dict]) -> str:
        """Generate SRT format subtitles"""
        srt_content = []
        for i, segment in enumerate(segments, 1):
            start_time = self._format_timestamp(segment.get('start', 0))
            end_time = self._format_timestamp(segment.get('end', 0))
            text = segment.get('text', '').strip()
            
            srt_content.append(f"{i}\n{start_time} --> {end_time}\n{text}\n")
        
        return "\n".join(srt_content)
    
    def _generate_vtt(self, segments: List[Dict]) -> str:
        """Generate VTT format subtitles"""
        vtt_content = ["WEBVTT", ""]
        for segment in segments:
            start_time = self._format_timestamp_vtt(segment.get('start', 0))
            end_time = self._format_timestamp_vtt(segment.get('end', 0))
            text = segment.get('text', '').strip()
            
            vtt_content.append(f"{start_time} --> {end_time}\n{text}\n")
        
        return "\n".join(vtt_content)
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format timestamp for SRT (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _format_timestamp_vtt(self, seconds: float) -> str:
        """Format timestamp for VTT (HH:MM:SS.mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    
    async def process_video(
        self,
        youtube_url: str,
        video_title: str,
        video_id: str,
        playlist_id: str = None,
        playlist_title: str = None
    ) -> Dict[str, Any]:
        """
        Process a single video through the complete pipeline
        
        Args:
            youtube_url: YouTube video URL
            video_title: Video title
            video_id: YouTube video ID
            playlist_id: Optional playlist ID
            playlist_title: Optional playlist title
        
        Returns:
            Processing result
        """
        temp_dir = tempfile.mkdtemp()
        audio_path = os.path.join(temp_dir, f"{video_id}.wav")
        
        try:
            # Step 1: Download and extract audio
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing: {video_title}")
            logger.info(f"{'='*60}")
            logger.info("Step 1: Extracting audio from video...")
            
            if not self.download_video_audio(youtube_url, audio_path):
                return {
                    "success": False,
                    "error": "Failed to download/extract audio"
                }
            
            # Step 2: Transcribe with Whisper
            logger.info("Step 2: Transcribing with Whisper ASR...")
            whisper_result = self.transcribe_with_whisper(audio_path)
            
            if not whisper_result.get("success"):
                return {
                    "success": False,
                    "error": whisper_result.get("error", "Whisper transcription failed")
                }
            
            raw_transcript = whisper_result.get("transcript", "")
            segments = whisper_result.get("segments", [])
            
            # Step 3: Enhance with LLM
            logger.info("Step 3: Enhancing transcript with LLM...")
            llm_result = await self.enhance_with_llm(raw_transcript, video_title)
            enhanced_transcript = llm_result.get("enhanced_transcript", raw_transcript)
            
            # Step 4: Generate subtitle files
            logger.info("Step 4: Generating subtitle files...")
            srt_path = os.path.join(temp_dir, f"{video_id}.srt")
            vtt_path = os.path.join(temp_dir, f"{video_id}.vtt")
            
            self.generate_subtitle_file(segments, srt_path, "srt")
            self.generate_subtitle_file(segments, vtt_path, "vtt")
            
            # Step 5: Store in Supabase
            logger.info("Step 5: Storing in Supabase...")
            storage_result = await self._store_transcript(
                video_id=video_id,
                youtube_url=youtube_url,
                title=video_title,
                raw_transcript=raw_transcript,
                enhanced_transcript=enhanced_transcript,
                segments=segments,
                srt_path=srt_path,
                vtt_path=vtt_path,
                playlist_id=playlist_id,
                playlist_title=playlist_title,
                metadata={
                    "language": self.language,
                    "whisper_model": self.whisper_model,
                    "duration": whisper_result.get("duration", 0),
                    "llm_enhanced": llm_result.get("enhanced", False)
                }
            )
            
            # Cleanup temp files
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except:
                pass
            
            if storage_result.get("success"):
                logger.info("✓ Successfully processed and stored!")
                return {
                    "success": True,
                    "video_id": video_id,
                    "title": video_title,
                    "transcript_length": len(enhanced_transcript),
                    "segments_count": len(segments)
                }
            else:
                return {
                    "success": False,
                    "error": storage_result.get("error")
                }
                
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            # Cleanup
            try:
                if os.path.exists(temp_dir):
                    import shutil
                    shutil.rmtree(temp_dir)
            except:
                pass
    
    async def _store_transcript(
        self,
        video_id: str,
        youtube_url: str,
        title: str,
        raw_transcript: str,
        enhanced_transcript: str,
        segments: List[Dict],
        srt_path: str,
        vtt_path: str,
        playlist_id: str = None,
        playlist_title: str = None,
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """Store transcript in Supabase"""
        try:
            # Check if bucket exists, create if not
            try:
                buckets = self.supabase_client.storage.list_buckets()
                bucket_exists = any(b.name == self.bucket_name for b in buckets)
                if not bucket_exists:
                    logger.warning(f"Bucket '{self.bucket_name}' does not exist. Storage uploads will be skipped.")
                    logger.warning("Please create the bucket manually in Supabase Dashboard:")
                    logger.warning(f"  1. Go to Storage → Create Bucket")
                    logger.warning(f"  2. Name: {self.bucket_name}")
                    logger.warning(f"  3. Public: Yes")
                    logger.warning(f"  4. Click Create")
            except Exception as e:
                logger.warning(f"Could not check bucket existence: {e}")
            
            # Upload subtitle files to storage (skip if bucket doesn't exist)
            srt_filename = f"playlists/{playlist_id or 'single'}/{video_id}.srt"
            vtt_filename = f"playlists/{playlist_id or 'single'}/{video_id}.vtt"
            storage_success = True
            
            try:
                # Upload SRT
                with open(srt_path, 'rb') as f:
                    self.supabase_client.storage.from_(self.bucket_name).upload(
                        srt_filename,
                        f.read(),
                        file_options={"content-type": "text/plain", "upsert": "true"}
                    )
                
                # Upload VTT
                with open(vtt_path, 'rb') as f:
                    self.supabase_client.storage.from_(self.bucket_name).upload(
                        vtt_filename,
                        f.read(),
                        file_options={"content-type": "text/vtt", "upsert": "true"}
                    )
                
                # Store full transcript in storage
                full_transcript_path = f"playlists/{playlist_id or 'single'}/{video_id}_transcript.txt"
                self.supabase_client.storage.from_(self.bucket_name).upload(
                    full_transcript_path,
                    enhanced_transcript.encode('utf-8'),
                    file_options={"content-type": "text/plain", "upsert": "true"}
                )
            except Exception as storage_error:
                logger.warning(f"Storage upload failed (bucket may not exist): {storage_error}")
                storage_success = False
                # Set placeholder URLs
                srt_filename = f"local/{video_id}.srt"
                vtt_filename = f"local/{video_id}.vtt"
            
            # Store in database (always try this, even if storage failed)
            insert_data = {
                "video_id": video_id,
                "youtube_url": youtube_url,
                "title": title,
                "playlist_id": playlist_id or "single",
                "playlist_title": playlist_title or "Individual Videos",
                "raw_transcript": raw_transcript[:10000],  # First 10K chars
                "enhanced_transcript": enhanced_transcript[:10000],  # First 10K chars
                "full_transcript_storage_path": f"playlists/{playlist_id or 'single'}/{video_id}_transcript.txt",
                "srt_storage_path": srt_filename,
                "vtt_storage_path": vtt_filename,
                "srt_url": f"https://jlfqzcaospvspmzbvbxd.supabase.co/storage/v1/object/public/{self.bucket_name}/{srt_filename}" if storage_success else "local",
                "vtt_url": f"https://jlfqzcaospvspmzbvbxd.supabase.co/storage/v1/object/public/{self.bucket_name}/{vtt_filename}" if storage_success else "local",
                "segments_count": len(segments),
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Insert into database
            result = self.supabase_client.table("telugu_transcripts").insert(insert_data).execute()
            
            return {
                "success": True,
                "id": result.data[0]['id'] if result.data else None,
                "storage_uploaded": storage_success
            }
            
        except Exception as e:
            logger.error(f"Error storing transcript: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process_channel(
        self,
        channel_url: str,
        max_playlists: Optional[int] = None,
        max_videos_per_playlist: Optional[int] = None
    ) -> Dict[str, Any]:
        """Process all playlists from a channel"""
        logger.info(f"Starting Telugu transcription pipeline for: {channel_url}")
        
        # Extract playlists
        playlists = self.playlist_extractor.get_channel_playlists(channel_url)
        if max_playlists:
            playlists = playlists[:max_playlists]
        
        logger.info(f"Found {len(playlists)} playlists")
        
        results = {
            "total_playlists": len(playlists),
            "processed_videos": 0,
            "failed_videos": 0,
            "playlist_results": []
        }
        
        for playlist in playlists:
            logger.info(f"\nProcessing playlist: {playlist['title']}")
            
            videos = self.playlist_extractor.get_playlist_videos(
                playlist['url'],
                max_results=max_videos_per_playlist
            )
            
            playlist_result = {
                "playlist_id": playlist['playlist_id'],
                "playlist_title": playlist['title'],
                "total_videos": len(videos),
                "processed": 0,
                "failed": 0
            }
            
            for video in videos:
                result = await self.process_video(
                    video['url'],
                    video['title'],
                    video.get('video_id', ''),
                    playlist['playlist_id'],
                    playlist['title']
                )
                
                if result.get("success"):
                    playlist_result["processed"] += 1
                    results["processed_videos"] += 1
                else:
                    playlist_result["failed"] += 1
                    results["failed_videos"] += 1
                
                # Delay between videos
                await asyncio.sleep(2)
            
            results["playlist_results"].append(playlist_result)
        
        return results


async def main():
    """Main entry point"""
    supabase_url = os.getenv("SUPABASE_URL", "https://jlfqzcaospvspmzbvbxd.supabase.co")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_key:
        print("Error: SUPABASE_KEY must be set")
        sys.exit(1)
    
    pipeline = TeluguTranscriptionPipeline(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        whisper_model="base",  # Use 'large' for better accuracy
        language="te"  # Telugu
    )
    
    channel_url = "https://www.youtube.com/@srichagantikoteswararaogar4451"
    
    results = await pipeline.process_channel(
        channel_url=channel_url,
        max_playlists=1,  # Start with 1 playlist for testing
        max_videos_per_playlist=1  # Start with 1 video for testing
    )
    
    print("\n" + "="*60)
    print("PIPELINE COMPLETE")
    print("="*60)
    print(f"Processed videos: {results['processed_videos']}")
    print(f"Failed videos: {results['failed_videos']}")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

