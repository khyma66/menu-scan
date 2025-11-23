#!/usr/bin/env python3
"""
OpenRouter MCP Server for Menu OCR integration
Provides access to OpenRouter's models including Qwen for better OCR results
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
logger = logging.getLogger("openrouter-mcp-server")

# Initialize the server
server = Server("openrouter-mcp")

class OpenRouterService:
    """Service to interact with OpenRouter API"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.timeout = 60
        
        if not self.api_key:
            logger.error("OPENROUTER_API_KEY not set in environment")
            
        # Available models for different OCR tasks
        self.models = {
            "qwen_vision": "qwen/qwen2.5-vl-32b-instruct:free",
            "qwen_coding": "qwen/qwen-2.5-coder-32b-instruct:free",
            "claude_vision": "anthropic/claude-3.5-sonnet",
            "gpt4_vision": "openai/gpt-4o"
        }

    async def process_vision_ocr(self, image_data: bytes, prompt: str = None) -> Dict[str, Any]:
        """
        Process image for OCR using OpenRouter's vision models
        
        Args:
            image_data: Raw image bytes
            prompt: Custom prompt for extraction
            
        Returns:
            Dict containing OCR results
        """
        try:
            if not self.api_key:
                return {"error": "OpenRouter API key not configured"}
            
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
                            "description": "Description if available"
                        }
                    ],
                    "restaurant_info": {
                        "name": "Restaurant name if visible",
                        "cuisine_type": "Type of cuisine if identifiable"
                    }
                }
                
                Only include information that is clearly visible in the image."""
            
            # Convert image to base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            # Prepare request data
            request_data = {
                "model": self.models["qwen_vision"],
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_b64}"
                                }
                            }
                        ]
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 2000
            }
            
            # Make API call
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://menu-ocr.com",
                        "X-Title": "Menu OCR Service"
                    },
                    json=request_data
                )
                
                response.raise_for_status()
                result = response.json()
                
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    
                    # Try to parse JSON response
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        # If not JSON, return as raw text
                        return {"raw_text": content, "menu_items": [], "error": "Could not parse as JSON"}
                else:
                    return {"error": "Invalid API response"}
                    
        except httpx.TimeoutException:
            logger.error("OpenRouter vision processing timed out")
            return {"error": "Processing timeout"}
        except Exception as e:
            logger.error(f"OpenRouter processing failed: {e}")
            return {"error": str(e)}

    async def enhance_ocr_text(self, raw_text: str, enhancement_type: str = "menu_analysis") -> Dict[str, Any]:
        """
        Enhance OCR text using language models
        
        Args:
            raw_text: Raw OCR text to enhance
            enhancement_type: Type of enhancement (menu_analysis, cleanup, etc.)
            
        Returns:
            Enhanced text data
        """
        try:
            if not self.api_key:
                return {"error": "OpenRouter API key not configured"}
            
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
                "model": self.models["qwen_coding"],
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 2000
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=request_data
                )
                
                response.raise_for_status()
                result = response.json()
                
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        return {"enhanced_text": content, "error": "Could not parse as JSON"}
                else:
                    return {"error": "Invalid API response"}
                    
        except Exception as e:
            logger.error(f"Text enhancement failed: {e}")
            return {"error": str(e)}

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available OpenRouter tools"""
    return [
        types.Tool(
            name="vision_ocr",
            description="Process images for OCR using OpenRouter's vision models",
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
                    }
                },
                "required": ["image_data"]
            }
        ),
        types.Tool(
            name="enhance_ocr_text",
            description="Enhance OCR text using language models",
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
            name="check_status",
            description="Check OpenRouter service status and available models",
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
        openrouter_service = OpenRouterService()
        
        if not openrouter_service.api_key:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": "OpenRouter API key not configured"}, indent=2)
            )]
        
        if name == "vision_ocr":
            image_data = arguments["image_data"]
            prompt = arguments.get("prompt")
            
            # Decode base64 image
            try:
                decoded_image = base64.b64decode(image_data)
            except Exception as e:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": f"Invalid base64 image data: {e}"}, indent=2)
                )]
            
            result = await openrouter_service.process_vision_ocr(decoded_image, prompt)
            
        elif name == "enhance_ocr_text":
            raw_text = arguments["raw_text"]
            enhancement_type = arguments.get("enhancement_type", "menu_analysis")
            
            result = await openrouter_service.enhance_ocr_text(raw_text, enhancement_type)
            
        elif name == "check_status":
            result = {
                "status": "active",
                "timestamp": datetime.utcnow().isoformat(),
                "api_key_configured": bool(openrouter_service.api_key),
                "available_models": list(openrouter_service.models.keys()),
                "base_url": openrouter_service.base_url
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
    return f"OpenRouter MCP Server Resource: {uri}"

async def main():
    """Main function to run the server"""
    logger.info("Starting OpenRouter MCP Server...")
    
    # Check for API key
    if not os.getenv("OPENROUTER_API_KEY"):
        logger.error("OPENROUTER_API_KEY environment variable is required")
        return
    
    # Run the server using stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="openrouter-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())