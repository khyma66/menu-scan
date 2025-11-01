"""OCR text parsing utilities."""

import re
from typing import List, Dict


def extract_menu_items(raw_text: str) -> List[Dict]:
    """
    Extract menu items from raw OCR text.
    
    Args:
        raw_text: Raw text from OCR processing
        
    Returns:
        List of menu items with name, price, description, category
    """
    menu_items = []
    lines = raw_text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue
        
        # Look for price patterns
        price_match = re.search(r'[\$£€¥₹]\s*(\d+\.?\d*)', line)
        price = price_match.group() if price_match else None
        
        # Extract item name (text before price)
        if price_match:
            name = line[:price_match.start()].strip()
        else:
            # Try to split on hyphens or other separators
            parts = re.split(r'[-–—]', line, 1)
            name = parts[0].strip()
        
        # Clean up the name
        name = re.sub(r'^\d+[.)]\s*', '', name)  # Remove numbered bullets
        name = re.sub(r'^[•\-\*]\s*', '', name)  # Remove bullet points
        
        if len(name) >= 3:
            menu_items.append({
                "name": name,
                "price": price,
                "description": None,
                "category": None
            })
    
    return menu_items if menu_items else [
        {"name": raw_text[:100], "price": None, "description": None, "category": None}
    ]

