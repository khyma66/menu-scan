"""
Test Telugu transcription quality
Downloads a short test video and verifies Telugu transcription accuracy
"""

import asyncio
import os
import sys
import tempfile
from dotenv import load_dotenv

from telugu_transcription_pipeline import TeluguTranscriptionPipeline

load_dotenv()


def check_telugu_text(text: str) -> dict:
    """Check if text contains proper Telugu characters"""
    # Telugu Unicode range: U+0C00 to U+0C7F
    telugu_chars = [chr(i) for i in range(0x0C00, 0x0C80)]
    telugu_count = sum(1 for char in text if char in telugu_chars)
    total_chars = len([c for c in text if c.isalnum() or c.isspace()])
    
    # Check for common Telugu words/patterns
    telugu_patterns = [
        'అ', 'ఆ', 'ఇ', 'ఈ', 'ఉ', 'ఊ', 'ఎ', 'ఏ', 'ఐ', 'ఒ', 'ఓ', 'ఔ',
        'క', 'ఖ', 'గ', 'ఘ', 'చ', 'ఛ', 'జ', 'ఝ', 'ట', 'ఠ', 'డ', 'ఢ',
        'త', 'థ', 'ద', 'ధ', 'న', 'ప', 'ఫ', 'బ', 'భ', 'మ', 'య', 'ర',
        'ల', 'వ', 'శ', 'ష', 'స', 'హ', 'ళ', 'క్ష', 'ఱ'
    ]
    
    has_telugu = any(pattern in text for pattern in telugu_patterns)
    
    return {
        "has_telugu": has_telugu,
        "telugu_char_count": telugu_count,
        "total_chars": total_chars,
        "telugu_percentage": (telugu_count / total_chars * 100) if total_chars > 0 else 0,
        "sample": text[:200]
    }


async def test_telugu_transcription():
    """Test Telugu transcription on a sample video"""
    supabase_url = os.getenv("SUPABASE_URL", "https://jlfqzcaospvspmzbvbxd.supabase.co")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_key:
        print("Error: SUPABASE_KEY must be set")
        sys.exit(1)
    
    print("="*60)
    print("Telugu Transcription Quality Test")
    print("="*60)
    
    pipeline = TeluguTranscriptionPipeline(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        whisper_model="base",
        language="te"  # Telugu
    )
    
    # Test with a known Telugu video (short clip)
    test_video_url = "https://www.youtube.com/watch?v=kyN-WQIqNgw"  # From the channel
    
    print(f"\nTesting video: {test_video_url}")
    print("This may take a few minutes...\n")
    
    # Process video
    result = await pipeline.process_video(
        youtube_url=test_video_url,
        video_title="Telugu Test Video",
        video_id="test_telugu_001"
    )
    
    if result.get("success"):
        print("\n" + "="*60)
        print("TRANSCRIPTION COMPLETE")
        print("="*60)
        
        # Get the stored transcript
        stored = pipeline.supabase_client.table("telugu_transcripts").select("*").eq("video_id", "test_telugu_001").execute()
        
        if stored.data:
            transcript = stored.data[0]
            raw_text = transcript.get("raw_transcript", "")
            enhanced_text = transcript.get("enhanced_transcript", "")
            
            print("\n1. RAW TRANSCRIPT ANALYSIS:")
            raw_check = check_telugu_text(raw_text)
            print(f"   Has Telugu characters: {raw_check['has_telugu']}")
            print(f"   Telugu characters: {raw_check['telugu_char_count']}/{raw_check['total_chars']}")
            print(f"   Telugu percentage: {raw_check['telugu_percentage']:.1f}%")
            print(f"   Sample: {raw_check['sample']}")
            
            print("\n2. ENHANCED TRANSCRIPT ANALYSIS:")
            enhanced_check = check_telugu_text(enhanced_text)
            print(f"   Has Telugu characters: {enhanced_check['has_telugu']}")
            print(f"   Telugu characters: {enhanced_check['telugu_char_count']}/{enhanced_check['total_chars']}")
            print(f"   Telugu percentage: {enhanced_check['telugu_percentage']:.1f}%")
            print(f"   Sample: {enhanced_check['sample']}")
            
            print("\n3. QUALITY ASSESSMENT:")
            if raw_check['telugu_percentage'] > 50:
                print("   ✓ Good Telugu transcription detected")
            elif raw_check['telugu_percentage'] > 20:
                print("   ⚠ Mixed content (some Telugu detected)")
            else:
                print("   ✗ Poor Telugu transcription (mostly non-Telugu)")
            
            print(f"\n4. SEGMENTS: {transcript.get('segments_count', 0)}")
            print(f"5. METADATA: {transcript.get('metadata', {})}")
            
        else:
            print("Error: Transcript not found in database")
    else:
        print("\n✗ TRANSCRIPTION FAILED")
        print(f"Error: {result.get('error')}")
    
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_telugu_transcription())
