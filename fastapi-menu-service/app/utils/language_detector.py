"""Language detection for European languages."""

import re
from typing import Optional, List

# European language codes for Tesseract
EUROPEAN_LANGUAGES = {
    "en": "English",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "pl": "Polish",
    "ru": "Russian",
    "uk": "Ukrainian",
    "cs": "Czech",
    "sk": "Slovak",
    "ro": "Romanian",
    "hu": "Hungarian",
    "bg": "Bulgarian",
    "hr": "Croatian",
    "sr": "Serbian",
    "sv": "Swedish",
    "no": "Norwegian",
    "da": "Danish",
    "fi": "Finnish",
    "et": "Estonian",
    "lv": "Latvian",
    "lt": "Lithuanian",
    "el": "Greek",
    "tr": "Turkish",
}

# Common words/phrases by language for detection
LANGUAGE_HINTS = {
    "en": ["the", "and", "menu", "price", "dollars", "euros"],
    "fr": ["le", "la", "les", "menu", "prix", "euros", "francs"],
    "de": ["der", "die", "das", "menu", "preis", "euros"],
    "es": ["el", "la", "menú", "precio", "euros"],
    "it": ["il", "la", "menu", "prezzo", "euros"],
    "pt": ["o", "a", "menu", "preço", "euros"],
    "nl": ["de", "het", "menu", "prijs", "euros"],
    "pl": ["menu", "cena", "złoty"],
    "ru": ["меню", "цена", "рубль"],
    "sv": ["meny", "pris", "kronor"],
    "da": ["menu", "pris", "kroner"],
    "no": ["meny", "pris", "kroner"],
    "fi": ["ruokalista", "hinta", "eurot"],
    "el": ["μενού", "τιμή", "ευρώ"],
}


def detect_european_language(text: str) -> str:
    """
    Detect European language from text.
    
    Args:
        text: Raw OCR text
        
    Returns:
        Language code (defaults to 'en' if not detected)
    """
    if not text or len(text.strip()) < 10:
        return "en"  # Default to English
    
    text_lower = text.lower()
    
    # Count matches for each language
    language_scores = {}
    
    for lang_code, hints in LANGUAGE_HINTS.items():
        score = sum(1 for hint in hints if hint in text_lower)
        if score > 0:
            language_scores[lang_code] = score
    
    # Return language with highest score, or default to English
    if language_scores:
        detected_lang = max(language_scores, key=language_scores.get)
        if language_scores[detected_lang] >= 1:
            return detected_lang
    
    # Fallback: Check for common European characters
    # Cyrillic
    if re.search(r'[А-Яа-я]', text):
        return "ru"
    
    # Greek
    if re.search(r'[Α-Ωα-ω]', text):
        return "el"
    
    # Default to English
    return "en"


def get_tesseract_language_code(lang_code: str) -> str:
    """
    Get Tesseract language code.
    
    Args:
        lang_code: ISO language code
        
    Returns:
        Tesseract language code
    """
    # Tesseract uses ISO codes, but some variations exist
    return lang_code


def get_available_languages() -> List[str]:
    """Get list of available European language codes."""
    return list(EUROPEAN_LANGUAGES.keys())


def is_european_language(lang_code: str) -> bool:
    """Check if language code is a European language."""
    return lang_code in EUROPEAN_LANGUAGES

