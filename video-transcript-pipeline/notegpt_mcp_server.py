"""
MCP Server for NoteGPT YouTube transcript extraction
This server provides tools to interact with NoteGPT.io for extracting video transcripts
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from playwright.async_api import async_playwright, Browser, Page
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# NoteGPT workspace URL
NOTEGPT_WORKSPACE_URL = "https://notegpt.io/workspace/youtube"

# Global browser instance
_browser: Optional[Browser] = None
_page: Optional[Page] = None
_playwright = None

async def get_browser() -> tuple[Browser, Page]:
    """Get or create browser instance"""
    global _browser, _page, _playwright
    
    if _browser is None:
        _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch(headless=True)
        _page = await _browser.new_page()
        await _page.goto(NOTEGPT_WORKSPACE_URL)
        await asyncio.sleep(3)  # Wait for page to load
    
    return _browser, _page

async def extract_transcript(youtube_url: str) -> Dict[str, Any]:
    """Extract transcript from YouTube URL using NoteGPT"""
    try:
        browser, page = await get_browser()
        
        # Find the input field and paste URL
        # Try multiple selectors for robustness
        input_selectors = [
            'input[type="text"]',
            'input[placeholder*="youtube" i]',
            'input[placeholder*="URL" i]',
            'input[placeholder*="link" i]',
            'textarea',
            'input'
        ]
        
        input_element = None
        used_selector = None
        for selector in input_selectors:
            try:
                input_element = await page.wait_for_selector(selector, timeout=5000, state="visible")
                if input_element:
                    used_selector = selector
                    break
            except:
                continue
        
        if not input_element or not used_selector:
            raise Exception("Could not find input field on NoteGPT page")
        
        # Clear and fill the input
        await page.fill(used_selector, youtube_url)
        
        # Submit the form
        submit_selectors = [
            'button[type="submit"]',
            'button:has-text("Submit")',
            'button:has-text("Extract")',
            'button:has-text("Get")',
            'button[aria-label*="submit" i]'
        ]
        
        submitted = False
        for btn_selector in submit_selectors:
            try:
                submit_button = await page.query_selector(btn_selector)
                if submit_button:
                    await submit_button.click()
                    submitted = True
                    break
            except:
                continue
        
        if not submitted:
            # Try pressing Enter
            await page.press(used_selector, "Enter")
        
        # Wait for transcript to be generated (with timeout)
        await asyncio.sleep(5)
        
        # Try multiple selectors for transcript
        transcript_selectors = [
            '[data-testid="transcript"]',
            '.transcript',
            '#transcript',
            '[class*="transcript" i]',
            '[class*="content" i]',
            'article',
            'main',
            'div[role="main"]'
        ]
        
        transcript_text = ""
        video_title = "Untitled"
        
        for selector in transcript_selectors:
            try:
                element = await page.wait_for_selector(selector, timeout=10000, state="visible")
                if element:
                    transcript_text = await element.inner_text()
                    if len(transcript_text) > 100:  # Ensure we got meaningful content
                        break
            except:
                continue
        
        # Try to get video title
        title_selectors = ['h1', 'h2', '[class*="title" i]', '[data-testid="title"]']
        for title_selector in title_selectors:
            try:
                title_element = await page.query_selector(title_selector)
                if title_element:
                    title_text = await title_element.inner_text()
                    if title_text and title_text.strip():
                        video_title = title_text.strip()
                        break
            except:
                continue
        
        if not transcript_text or len(transcript_text) < 50:
            raise Exception("Could not extract transcript text from page")
        
        return {
            "success": True,
            "youtube_url": youtube_url,
            "title": video_title,
            "transcript": transcript_text.strip(),
            "extracted_at": time.time()
        }
        
    except Exception as e:
        logger.error(f"Error extracting transcript: {e}")
        raise

# Create MCP server
server = Server("notegpt-mcp")

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools"""
    return [
        Tool(
            name="extract_transcript",
            description="Extract transcript from a YouTube video URL using NoteGPT.io",
            inputSchema={
                "type": "object",
                "properties": {
                    "youtube_url": {
                        "type": "string",
                        "description": "YouTube video URL to extract transcript from (e.g., https://www.youtube.com/watch?v=VIDEO_ID)"
                    }
                },
                "required": ["youtube_url"]
            }
        ),
        Tool(
            name="batch_extract_transcripts",
            description="Extract transcripts from multiple YouTube video URLs",
            inputSchema={
                "type": "object",
                "properties": {
                    "youtube_urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of YouTube video URLs"
                    }
                },
                "required": ["youtube_urls"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""
    if name == "extract_transcript":
        youtube_url = arguments.get("youtube_url")
        if not youtube_url:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "youtube_url is required"}, indent=2)
            )]
        
        try:
            result = await extract_transcript(youtube_url)
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        except Exception as e:
            logger.error(f"Error extracting transcript: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({"error": str(e), "success": False}, indent=2)
            )]
    
    elif name == "batch_extract_transcripts":
        youtube_urls = arguments.get("youtube_urls", [])
        if not youtube_urls:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "youtube_urls is required"}, indent=2)
            )]
        
        results = []
        for url in youtube_urls:
            try:
                result = await extract_transcript(url)
                results.append(result)
                await asyncio.sleep(2)  # Delay between requests
            except Exception as e:
                results.append({
                    "success": False,
                    "youtube_url": url,
                    "error": str(e)
                })
        
        summary = {
            "total": len(youtube_urls),
            "successful": sum(1 for r in results if r.get("success", False)),
            "failed": sum(1 for r in results if not r.get("success", False)),
            "results": results
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(summary, indent=2)
        )]
    
    else:
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"Unknown tool: {name}"}, indent=2)
        )]

async def cleanup():
    """Cleanup browser resources"""
    global _browser, _playwright
    if _browser:
        await _browser.close()
        _browser = None
    if _playwright:
        await _playwright.stop()
        _playwright = None

async def main():
    """Main entry point for MCP server"""
    import signal
    
    def signal_handler(sig, frame):
        logger.info("Shutting down...")
        asyncio.create_task(cleanup())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())

