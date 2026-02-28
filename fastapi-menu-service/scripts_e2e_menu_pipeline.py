import asyncio
import json
from pathlib import Path

from app.services.gemini_groq_menu_service import GeminiGroqMenuService


def pick_image() -> Path:
    candidates = [
        Path("/Users/mohanakrishnanarsupalli/menu-ocr/tests/assets/test_menu_clear.png"),
        Path("/Users/mohanakrishnanarsupalli/menu-ocr/tests/assets/test_menu.png"),
        Path("/Users/mohanakrishnanarsupalli/menu-ocr/tests/assets/emulator_screenshot.png"),
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError("No test menu image found under tests/assets")


async def main() -> None:
    image_path = pick_image()
    image_bytes = image_path.read_bytes()

    service = GeminiGroqMenuService()
    result = await service.process_menu(
        image_bytes=image_bytes,
        language_hint="auto",
        health_profile={
            "health_conditions": ["diabetes"],
            "allergies": ["peanut"],
            "dietary_preferences": ["high-protein"],
            "medical_notes": "avoid added sugar",
        },
        use_groq_enhancement=True,
    )

    rows = result.get("menu_items", [])
    output = {
        "image": str(image_path),
        "pipeline": result.get("metadata", {}).get("pipeline"),
        "ocr_model": result.get("metadata", {}).get("ocr_model"),
        "enhancement_model": result.get("metadata", {}).get("enhancement_model"),
        "rows_count": len(rows),
        "sample": rows[0] if rows else None,
    }
    print(json.dumps(output, ensure_ascii=False)[:2000])


if __name__ == "__main__":
    asyncio.run(main())
