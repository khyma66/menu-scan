"""Tests for OCR processing."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.utils.ocr_parser import extract_menu_items

client = TestClient(app)


def test_ocr_endpoint_missing_url():
    """Test OCR endpoint with missing image URL."""
    response = client.post("/api/v1/ocr/process", json={
        "image_url": "",
    })
    assert response.status_code in [400, 422]


def test_ocr_endpoint_invalid_url():
    """Test OCR endpoint with invalid URL."""
    response = client.post("/api/v1/ocr/process", json={
        "image_url": "not-a-valid-url",
        "use_llm_enhancement": False,
        "language": "en"
    })
    assert response.status_code in [400, 422]


def test_extract_menu_items():
    """Test menu item extraction from text."""
    test_text = """
    MENU
    
    Pasta Carbonara - $18.99
    Classic Italian pasta with eggs, bacon, and parmesan cheese
    
    Margherita Pizza - $15.50
    Fresh mozzarella, tomato sauce, and basil
    
    Caesar Salad - $12.00
    Fresh romaine lettuce with caesar dressing
    """
    
    items = extract_menu_items(test_text)
    assert len(items) > 0
    assert any("carbonara" in item["name"].lower() for item in items)
    

def test_extract_menu_items_with_prices():
    """Test extraction with price patterns."""
    test_text = "Burger $12.99\nPizza $14.50\nSalad $8.00"
    items = extract_menu_items(test_text)
    assert len(items) >= 3
    prices = [item["price"] for item in items if item.get("price")]
    assert len(prices) > 0
    

@pytest.mark.skip(reason="Requires actual image URL and API keys")
def test_ocr_process_real_image():
    """Test OCR processing with real image - skipped in CI."""
    response = client.post("/api/v1/ocr/process", json={
        "image_url": "https://example.com/menu.jpg",
        "use_llm_enhancement": False,
        "language": "en"
    })
    # This test is skipped but structure is ready
    assert True

