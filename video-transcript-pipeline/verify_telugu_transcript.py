"""
Verify Telugu transcription quality from database
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client
import re

load_dotenv()


def verify_telugu_quality():
    """Verify Telugu transcription quality from stored transcripts"""
    supabase_url = os.getenv("SUPABASE_URL", "https://jlfqzcaospvspmzbvbxd.supabase.co")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_key:
        print("Error: SUPABASE_KEY must be set")
        sys.exit(1)
    
    client = create_client(supabase_url, supabase_key)
    
    print("="*60)
    print("Telugu Transcription Quality Verification")
    print("="*60)
    
    # Get transcripts from database
    result = client.table("telugu_transcripts").select("*").limit(5).execute()
    
    if not result.data:
        print("\n⚠ No transcripts found in database yet.")
        print("Pipeline may still be running...")
        return
    
    print(f"\nFound {len(result.data)} transcript(s) in database\n")
    
    # Telugu Unicode range
    telugu_range = '\u0C00-\u0C7F'
    
    for idx, transcript in enumerate(result.data, 1):
        print(f"\n{'='*60}")
        print(f"Transcript {idx}: {transcript.get('title', 'Unknown')}")
        print(f"{'='*60}")
        
        raw_text = transcript.get('raw_transcript', '') or ''
        enhanced_text = transcript.get('enhanced_transcript', '') or ''
        
        # Analyze raw transcript
        print(f"\n📝 Raw Transcript Analysis:")
        print(f"   Length: {len(raw_text)} characters")
        
        if raw_text:
            # Count Telugu characters
            telugu_chars = re.findall(f'[{telugu_range}]', raw_text)
            telugu_ratio = len(telugu_chars) / len(raw_text) if raw_text else 0
            
            print(f"   Telugu characters: {len(telugu_chars)}")
            print(f"   Telugu ratio: {telugu_ratio*100:.1f}%")
            
            # Check for non-Telugu scripts
            patterns = {
                'Arabic/Urdu': r'[ا-ي]',
                'Hindi/Devanagari': r'[अ-ह]',
                'English words': r'\b[A-Za-z]{10,}\b',
            }
            
            print(f"\n   Non-Telugu content:")
            for name, pattern in patterns.items():
                matches = re.findall(pattern, raw_text)
                if matches:
                    print(f"     ⚠ {name}: {len(matches)} occurrences")
                    if len(matches) <= 5:
                        print(f"       Examples: {matches[:3]}")
                else:
                    print(f"     ✓ No {name} found")
            
            # Show preview
            print(f"\n   Preview (first 300 chars):")
            print(f"   {'-'*58}")
            preview = raw_text[:300].replace('\n', ' ')
            print(f"   {preview}")
            print(f"   {'-'*58}")
        
        # Analyze enhanced transcript
        if enhanced_text and enhanced_text != raw_text:
            print(f"\n✨ Enhanced Transcript Analysis:")
            print(f"   Length: {len(enhanced_text)} characters")
            
            telugu_chars_enh = re.findall(f'[{telugu_range}]', enhanced_text)
            telugu_ratio_enh = len(telugu_chars_enh) / len(enhanced_text) if enhanced_text else 0
            
            print(f"   Telugu characters: {len(telugu_chars_enh)}")
            print(f"   Telugu ratio: {telugu_ratio_enh*100:.1f}%")
            
            print(f"\n   Preview (first 300 chars):")
            print(f"   {'-'*58}")
            preview_enh = enhanced_text[:300].replace('\n', ' ')
            print(f"   {preview_enh}")
            print(f"   {'-'*58}")
        
        # Check metadata
        metadata = transcript.get('metadata', {})
        if metadata:
            print(f"\n📊 Metadata:")
            print(f"   Language: {metadata.get('language', 'unknown')}")
            print(f"   Whisper Model: {metadata.get('whisper_model', 'unknown')}")
            print(f"   Duration: {metadata.get('duration', 0):.2f} seconds")
            print(f"   LLM Enhanced: {metadata.get('llm_enhanced', False)}")
        
        # Quality assessment
        print(f"\n✅ Quality Assessment:")
        if raw_text:
            telugu_ratio = len(re.findall(f'[{telugu_range}]', raw_text)) / len(raw_text) if raw_text else 0
            if telugu_ratio > 0.7:
                print(f"   ✓ Good Telugu content ({telugu_ratio*100:.1f}%)")
            elif telugu_ratio > 0.4:
                print(f"   ⚠ Mixed content ({telugu_ratio*100:.1f}% Telugu)")
            else:
                print(f"   ✗ Low Telugu content ({telugu_ratio*100:.1f}%)")
        
        print(f"\n   Segments: {transcript.get('segments_count', 0)}")
        print(f"   Created: {transcript.get('created_at', 'Unknown')}")
    
    print("\n" + "="*60)
    print("VERIFICATION COMPLETE")
    print("="*60)


if __name__ == "__main__":
    verify_telugu_quality()

