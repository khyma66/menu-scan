#!/usr/bin/env python3
"""
Gemini MCP Server for Menu OCR integration
Provides access to Google Gemini Vision models for OCR processing
"""

import asyncio
import json
import base64
import os
import logging
import httpx
from typing import Any, Dict, List, Optional
from datetime import datetime

# MCP server imports
try:
    from mcp.server import Server, NotificationOptions
    from mcp.server.models import InitializationOptions
    import mcp.server.stdio
    import mcp.types as types
except ImportError:
    print("Error: mcp package not installed. Please install: pip install mcp")
    import sys
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gemini-mcp-server")

# Initialize the server
server = Server("gemini-mcp")

class GeminiService:
    """Service to interact with Google Gemini API"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.timeout = 60
        
        if not self.api_key:
            logger.error("GEMINI_API_KEY not set in environment")
            
        # Available Gemini models (updated for 2025)
        self.models = {
            "gemini_flash": "gemini-2.5-flash",
            "gemini_pro": "gemini-2.5-pro"
        }

    async def process_vision_ocr(self, image_data: bytes, prompt: str = None, model: str = "gemini-2.5-flash") -> Dict[str, Any]:
        """
        Process image for OCR using Gemini Vision models
        
        Args:
            image_data: Raw image bytes
            prompt: Custom prompt for extraction
            model: Gemini model to use
            
        Returns:
            Dict containing OCR results
        """
        try:
            if not self.api_key:
                return {"error": "Gemini API key not configured"}
            
            # Default menu OCR prompt
            if not prompt:
                prompt = """Analyze this menu image and extract all visible text and menu items. 
                
                Return the following information in JSON format:
                {
                    "raw_text": "All extracted text from the image",
                    "menu_items": [
                        {
                            "name": "Item name",
                            "price": "Price if visible",
                            "category": "Category (appetizer, main, dessert, etc.)",
                            "description": "Description if available",
                            "ingredients": ["List of ingredients if mentioned"]
                        }
                    ],
                    "restaurant_info": {
                        "name": "Restaurant name if visible",
                        "cuisine_type": "Type of cuisine if identifiable"
                    }
                }
                
                Only include information that is clearly visible in the image. Return valid JSON only."""
            
            # Convert image to base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            # Detect image mime type from first bytes
            mime_type = "image/jpeg"
            if image_data[:8] == b'\x89PNG\r\n\x1a\n':
                mime_type = "image/png"
            elif image_data[:6] in (b'GIF87a', b'GIF89a'):
                mime_type = "image/gif"
            elif image_data[:4] == b'RIFF' and image_data[8:12] == b'WEBP':
                mime_type = "image/webp"
            
            # Prepare request data for Gemini API
            request_data = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            },
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": image_b64
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 4096,
                    "responseMimeType": "application/json"
                }
            }
            
            # Gemini API URL
            url = f"{self.base_url}/{model}:generateContent?key={self.api_key}"
            
            # Make API call
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    headers={
                        "Content-Type": "application/json"
                    },
                    json=request_data
                )
                
                response.raise_for_status()
                result = response.json()
                
                if "candidates" in result and len(result["candidates"]) > 0:
                    content = result["candidates"][0]["content"]["parts"][0]["text"]
                    
                    # Try to parse JSON response
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        # If not JSON, return as raw text
                        return {"raw_text": content, "menu_items": [], "error": "Could not parse as JSON"}
                else:
                    return {"error": "Invalid API response", "details": result}
                    
        except httpx.TimeoutException:
            logger.error("Gemini vision processing timed out")
            return {"error": "Processing timeout"}
        except httpx.HTTPStatusError as e:
            logger.error(f"Gemini API HTTP error: {e}")
            return {"error": f"HTTP error: {e.response.status_code}", "details": e.response.text}
        except Exception as e:
            logger.error(f"Gemini processing failed: {e}")
            return {"error": str(e)}

    async def enhance_ocr_text(self, raw_text: str, enhancement_type: str = "menu_analysis") -> Dict[str, Any]:
        """
        Enhance OCR text using Gemini language models
        
        Args:
            raw_text: Raw OCR text to enhance
            enhancement_type: Type of enhancement (menu_analysis, cleanup, etc.)
            
        Returns:
            Enhanced text data
        """
        try:
            if not self.api_key:
                return {"error": "Gemini API key not configured"}
            
            # Different prompts for different enhancement types
            prompts = {
                "menu_analysis": f"""Analyze this raw OCR text from a menu and extract structured menu information:
                
Raw OCR text:
{raw_text}

Return JSON with:
{{
    "restaurant_name": "Name of restaurant if identifiable",
    "menu_items": [
        {{
            "name": "Clean item name",
            "price": "Price if present",
            "category": "Category (appetizer, main, dessert, drink, etc.)",
            "description": "Any description found"
        }}
    ],
    "menu_sections": ["List of menu sections found"],
    "confidence": "High/Medium/Low based on text quality"
}}""",
                "cleanup": f"""Clean up this OCR text by fixing common OCR errors while preserving the original meaning:
                
Raw OCR text:
{raw_text}

Return only the cleaned text."""
            }
            
            prompt = prompts.get(enhancement_type, prompts["menu_analysis"])
            
            request_data = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 4096,
                    "responseMimeType": "application/json"
                }
            }
            
            url = f"{self.base_url}/gemini-2.5-flash:generateContent?key={self.api_key}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=request_data
                )
                
                response.raise_for_status()
                result = response.json()
                
                if "candidates" in result and len(result["candidates"]) > 0:
                    content = result["candidates"][0]["content"]["parts"][0]["text"]
                    
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        return {"enhanced_text": content, "error": "Could not parse as JSON"}
                else:
                    return {"error": "Invalid API response"}
                    
        except Exception as e:
            logger.error(f"Text enhancement failed: {e}")
            return {"error": str(e)}

    async def analyze_dietary_info(self, menu_items: List[Dict]) -> Dict[str, Any]:
        """
        Analyze menu items for dietary information
        
        Args:
            menu_items: List of menu items to analyze
            
        Returns:
            Dietary analysis results
        """
        try:
            if not self.api_key:
                return {"error": "Gemini API key not configured"}
            
            prompt = f"""Analyze these menu items for dietary information and allergens:

Menu items:
{json.dumps(menu_items, indent=2)}

Return JSON with:
{{
    "items_analysis": [
        {{
            "name": "Item name",
            "likely_allergens": ["common allergens based on ingredients"],
            "dietary_tags": ["vegetarian", "vegan", "gluten-free", etc.],
            "health_notes": "Any health considerations"
        }}
    ],
    "overall_summary": "Summary of dietary options available"
}}"""

            request_data = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 4096,
                    "responseMimeType": "application/json"
                }
            }
            
            url = f"{self.base_url}/gemini-2.5-flash:generateContent?key={self.api_key}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=request_data
                )
                
                response.raise_for_status()
                result = response.json()
                
                if "candidates" in result and len(result["candidates"]) > 0:
                    content = result["candidates"][0]["content"]["parts"][0]["text"]
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        return {"raw_analysis": content}
                else:
                    return {"error": "Invalid API response"}
                    
        except Exception as e:
            logger.error(f"Dietary analysis failed: {e}")
            return {"error": str(e)}

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available Gemini tools"""
    return [
        types.Tool(
            name="vision_ocr",
            description="Process images for OCR using Gemini Vision models (gemini-1.5-flash)",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_data": {
                        "type": "string",
                        "description": "Base64 encoded image data"
                    },
                    "prompt": {
                        "type": "string", 
                        "description": "Custom prompt for extraction (optional)"
                    },
                    "model": {
                        "type": "string",
                        "description": "Gemini model to use (gemini-2.5-flash, gemini-2.5-pro)",
                        "enum": ["gemini-2.5-flash", "gemini-2.5-pro"],
                        "default": "gemini-2.5-flash"
                    }
                },
                "required": ["image_data"]
            }
        ),
        types.Tool(
            name="enhance_ocr_text",
            description="Enhance OCR text using Gemini language models",
            inputSchema={
                "type": "object",
                "properties": {
                    "raw_text": {
                        "type": "string",
                        "description": "Raw OCR text to enhance"
                    },
                    "enhancement_type": {
                        "type": "string",
                        "description": "Type of enhancement (menu_analysis, cleanup)",
                        "enum": ["menu_analysis", "cleanup"],
                        "default": "menu_analysis"
                    }
                },
                "required": ["raw_text"]
            }
        ),
        types.Tool(
            name="analyze_dietary",
            description="Analyze menu items for dietary information and allergens",
            inputSchema={
                "type": "object",
                "properties": {
                    "menu_items": {
                        "type": "array",
                        "description": "List of menu items to analyze",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "ingredients": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    }
                },
                "required": ["menu_items"]
            }
        ),
        types.Tool(
            name="check_status",
            description="Check Gemini service status and available models",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls"""
    try:
        gemini_service = GeminiService()
        
        if not gemini_service.api_key:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": "Gemini API key not configured"}, indent=2)
            )]
        
        if name == "vision_ocr":
            image_data = arguments["image_data"]
            prompt = arguments.get("prompt")
            model = arguments.get("model", "gemini-1.5-flash")
            
            # Decode base64 image
            try:
                decoded_image = base64.b64decode(image_data)
            except Exception as e:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": f"Invalid base64 image data: {e}"}, indent=2)
                )]
            
            result = await gemini_service.process_vision_ocr(decoded_image, prompt, model)
            
        elif name == "enhance_ocr_text":
            raw_text = arguments["raw_text"]
            enhancement_type = arguments.get("enhancement_type", "menu_analysis")
            
            result = await gemini_service.enhance_ocr_text(raw_text, enhancement_type)
            
        elif name == "analyze_dietary":
            menu_items = arguments["menu_items"]
            
            result = await gemini_service.analyze_dietary_info(menu_items)
            
        elif name == "check_status":
            result = {
                "status": "active",
                "timestamp": datetime.utcnow().isoformat(),
                "api_key_configured": bool(gemini_service.api_key),
                "available_models": list(gemini_service.models.keys()),
                "base_url": gemini_service.base_url
            }
            
        else:
            result = {"error": f"Unknown tool: {name}"}
            
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
        
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, indent=2)
        )]

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Handle resource reading"""
    return f"Gemini MCP Server Resource: {uri}"

async def main():
    """Main function to run the server"""
    logger.info("Starting Gemini MCP Server...")
    
    # Check for API key
    if not os.getenv("GEMINI_API_KEY"):
        logger.error("GEMINI_API_KEY environment variable is required")
        return
    
    # Run the server using stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="gemini-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
