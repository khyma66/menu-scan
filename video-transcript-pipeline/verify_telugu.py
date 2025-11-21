"""
Verify Telugu script in transcription output
"""

def verify_telugu_script(text: str) -> dict:
    """Verify if text contains proper Telugu script"""
    # Telugu Unicode block: U+0C00 to U+0C7F
    telugu_range = range(0x0C00, 0x0C80)
    
    # Common Telugu characters
    telugu_chars = set()
    for i in telugu_range:
        telugu_chars.add(chr(i))
    
    # Count Telugu vs other scripts
    telugu_count = 0
    other_count = 0
    detected_scripts = set()
    
    for char in text:
        code = ord(char)
        if code in telugu_range:
            telugu_count += 1
        elif char.isalpha():
            # Check for other Indic scripts
            if 0x0900 <= code <= 0x097F:  # Devanagari (Hindi)
                detected_scripts.add("Devanagari")
            elif 0x0980 <= code <= 0x09FF:  # Bengali
                detected_scripts.add("Bengali")
            elif 0x0600 <= code <= 0x06FF:  # Arabic
                detected_scripts.add("Arabic")
            elif 0x0750 <= code <= 0x077F:  # Arabic Supplement
                detected_scripts.add("Arabic")
            elif 0xFB50 <= code <= 0xFDFF:  # Arabic Presentation Forms-A
                detected_scripts.add("Arabic")
            elif 0xFE70 <= code <= 0xFEFF:  # Arabic Presentation Forms-B
                detected_scripts.add("Arabic")
            elif 0x0600 <= code <= 0x06FF or 0x0750 <= code <= 0x077F:
                detected_scripts.add("Urdu/Arabic")
            other_count += 1
    
    total_chars = telugu_count + other_count
    telugu_percentage = (telugu_count / total_chars * 100) if total_chars > 0 else 0
    
    return {
        "is_telugu": telugu_percentage > 50,
        "telugu_count": telugu_count,
        "other_count": other_count,
        "telugu_percentage": telugu_percentage,
        "detected_scripts": list(detected_scripts),
        "sample": text[:300]
    }


if __name__ == "__main__":
    # Test with sample text
    test_texts = [
        "తెలుగు భాషలో వ్రాయబడింది",  # Proper Telugu
        "تانو ماتراانا بھلچن",  # Urdu/Arabic (wrong)
        "Vikti shankara chayar galavari",  # Romanized
    ]
    
    for i, text in enumerate(test_texts, 1):
        result = verify_telugu_script(text)
        print(f"\nTest {i}:")
        print(f"  Text: {text[:50]}...")
        print(f"  Is Telugu: {result['is_telugu']}")
        print(f"  Telugu %: {result['telugu_percentage']:.1f}%")
        print(f"  Detected scripts: {result['detected_scripts']}")

