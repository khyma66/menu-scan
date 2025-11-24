"""
MCP Server for Restaurant Discovery and Vision OCR
Provides restaurant search, menu analysis, and AI-powered image processing
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import base64
from vision_ocr_service import VisionOCRService

logger = logging.getLogger(__name__)

class RestaurantDiscoveryMCP:
    """MCP Server for restaurant discovery and vision OCR capabilities"""
    
    def __init__(self):
        self.vision_service = VisionOCRService()
        self.restaurant_api_url = "http://localhost:8001"  # Our restaurant discovery API
        self.supported_tools = {
            "search_restaurants": {
                "description": "Search for restaurants near a location by category",
                "parameters": {
                    "lat": {"type": "number", "description": "Latitude"},
                    "lng": {"type": "number", "description": "Longitude"},
                    "category": {"type": "string", "description": "Restaurant category"},
                    "radius": {"type": "number", "description": "Search radius in meters"}
                }
            },
            "analyze_menu_image": {
                "description": "Analyze menu image using AI vision to extract menu items",
                "parameters": {
                    "image_base64": {"type": "string", "description": "Base64 encoded image"},
                    "custom_prompt": {"type": "string", "description": "Custom analysis prompt"}
                }
            },
            "get_restaurant_details": {
                "description": "Get detailed information about a specific restaurant",
                "parameters": {
                    "place_id": {"type": "string", "description": "Google Places ID"}
                }
            },
            "check_vision_backends": {
                "description": "Check available vision processing backends and their health",
                "parameters": {}
            }
        }

    async def handle_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle MCP protocol requests"""
        try:
            if method == "tools/list":
                return await self._list_tools()
            elif method == "tools/call":
                return await self._call_tool(params)
            else:
                return self._error_response(f"Unknown method: {method}")
        except Exception as e:
            logger.error(f"MCP request handling error: {e}")
            return self._error_response(str(e))

    async def _list_tools(self) -> Dict[str, Any]:
        """List available MCP tools"""
        return {
            "tools": [
                {
                    "name": name,
                    "description": info["description"],
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "params": {
                                "type": "object",
                                "properties": info["parameters"]
                            }
                        }
                    }
                }
                for name, info in self.supported_tools.items()
            ]
        }

    async def _call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific tool"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "search_restaurants":
            return await self._search_restaurants(arguments)
        elif tool_name == "analyze_menu_image":
            return await self._analyze_menu_image(arguments)
        elif tool_name == "get_restaurant_details":
            return await self._get_restaurant_details(arguments)
        elif tool_name == "check_vision_backends":
            return await self._check_vision_backends()
        else:
            return self._error_response(f"Unknown tool: {tool_name}")

    async def _search_restaurants(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for restaurants near a location"""
        try:
            import httpx
            
            # Call our restaurant discovery API
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{self.restaurant_api_url}/api/restaurants/nearby", params={
                    "lat": params["lat"],
                    "lng": params["lng"],
                    "category": params.get("category"),
                    "radius": params.get("radius", 2000)
                })
                response.raise_for_status()
                result = response.json()
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Found {result['total_count']} restaurants near location ({params['lat']}, {params['lng']}):\n\n" + 
                                   "\n".join([
                                       f"- {r['name']} ({r['category']}) - {r['rating']}⭐ - {r['vicinity']}" 
                                       for r in result['restaurants'][:10]  # Limit to top 10
                                   ])
                        }
                    ]
                }
        except Exception as e:
            logger.error(f"Restaurant search error: {e}")
            return self._error_response(f"Failed to search restaurants: {e}")

    async def _analyze_menu_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze menu image using AI vision"""
        try:
            # Decode base64 image
            image_data = base64.b64decode(params["image_base64"])
            
            # Process with vision service
            result = await self.vision_service.process_menu_image(
                image_data, 
                params.get("custom_prompt")
            )
            
            if result.get("success"):
                # Format results for MCP response
                items_text = "\n".join([
                    f"- {item.get('name', 'Unknown')} - {item.get('price', 'Price not visible')}"
                    for item in result.get("extracted_items", [])
                ])
                
                response_text = f"Menu Analysis Results:\n\n"\
                               f"Restaurant: {result.get('restaurant_info', {}).get('name', 'Unknown')}\n"\
                               f"Cuisine: {result.get('restaurant_info', {}).get('cuisine', 'Unknown')}\n"\
                               f"Backend Used: {result.get('backend_used', 'Unknown')}\n\n"\
                               f"Extracted Menu Items:\n{items_text}\n\n"\
                               f"Full Text: {result.get('text', 'No text extracted')}"
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": response_text
                        }
                    ],
                    "isError": False
                }
            else:
                return self._error_response(f"Menu analysis failed: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Menu analysis error: {e}")
            return self._error_response(f"Failed to analyze menu image: {e}")

    async def _get_restaurant_details(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information about a restaurant"""
        try:
            import httpx
            
            place_id = params["place_id"]
            
            # Call restaurant details API
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{self.restaurant_api_url}/api/restaurants/{place_id}")
                response.raise_for_status()
                result = response.json()
                
                response_text = f"Restaurant Details:\n\n"\
                               f"Name: {result.get('name', 'Unknown')}\n"\
                               f"Rating: {result.get('rating', 'No rating')}\n"\
                               f"Price Level: {result.get('price_level', 'Not specified')}\n"\
                               f"Address: {result.get('address', 'Not available')}\n"\
                               f"Phone: {result.get('phone', 'Not available')}\n"\
                               f"Website: {result.get('website', 'Not available')}\n"\
                               f"Reviews Count: {result.get('reviews_count', 0)}"
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": response_text
                        }
                    ]
                }
        except Exception as e:
            logger.error(f"Restaurant details error: {e}")
            return self._error_response(f"Failed to get restaurant details: {e}")

    async def _check_vision_backends(self) -> Dict[str, Any]:
        """Check vision processing backends health"""
        try:
            health = await self.vision_service.check_backend_health()
            
            response_text = "Vision Processing Backends Status:\n\n"
            for backend, status in health.items():
                status_emoji = "✅" if status else "❌"
                response_text += f"{status_emoji} {backend.title()}: {'Available' if status else 'Unavailable'}\n"
            
            response_text += "\nNote: Local Ollama requires vision-capable models (qwen2-vl, llava, etc.)"
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": response_text
                    }
                ]
            }
        except Exception as e:
            logger.error(f"Backend health check error: {e}")
            return self._error_response(f"Failed to check backends: {e}")

    def _error_response(self, message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error: {message}"
                }
            ],
            "isError": True
        }

# MCP Server Protocol Implementation
class MCPServer:
    def __init__(self):
        self.restaurant_mcp = RestaurantDiscoveryMCP()
    
    async def handle_jsonrpc_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle JSON-RPC 2.0 requests"""
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {
                                "listChanged": True
                            }
                        },
                        "serverInfo": {
                            "name": "restaurant-discovery-mcp",
                            "version": "1.0.0"
                        }
                    }
                }
            elif method == "tools/list":
                result = await self.restaurant_mcp._list_tools()
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
            elif method == "tools/call":
                result = await self.restaurant_mcp._call_tool(params)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
        except Exception as e:
            logger.error(f"JSON-RPC handling error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }

# Server startup
async def main():
    """Main MCP server function"""
    mcp_server = MCPServer()
    logger.info("Starting Restaurant Discovery MCP Server...")
    
    # Test the restaurant API connection
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get("http://localhost:8001/health")
            logger.info(f"Restaurant API health check: {response.status_code}")
    except Exception as e:
        logger.warning(f"Restaurant API not available: {e}")
    
    # Start serving requests (this would be integrated with your HTTP server)
    logger.info("MCP Server ready for requests")

if __name__ == "__main__":
    asyncio.run(main())