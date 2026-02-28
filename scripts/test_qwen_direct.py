#!/usr/bin/env python3
"""
Direct test of Qwen Vision API
"""

import sys
import os
sys.path.append('fastapi-menu-service')

import asyncio
import base64
from app.services.qwen_vision_service import QwenVisionService

async def test_qwen():
    service = QwenVisionService()

    # Create a simple test image
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new('RGB', (300, 200), color='white')
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype('/System/Library/Fonts/Arial.ttf', 20)
    except:
        font = ImageFont.load_default()

    draw.text((20, 30), 'PIZZA MARGAHERITA - $12.99', fill='black', font=font)
    draw.text((20, 70), 'CHEESEBURGER - $8.50', fill='black', font=font)
    draw.text((20, 110), 'COKE - $2.75', fill='black', font=font)

    # Convert to bytes
    from io import BytesIO
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_bytes = buffer.getvalue()

    print(f"Testing Qwen API with image size: {len(img_bytes)} bytes")
    print(f"API Key configured: {bool(service.api_key)}")

    result = await service.process_menu_image(img_bytes)

    print("Qwen API Response:")
    print(result)

if __name__ == "__main__":
    asyncio.run(test_qwen())