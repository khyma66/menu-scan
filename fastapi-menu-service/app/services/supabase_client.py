"""Supabase client service for database operations."""

from supabase import create_client, Client
from app.config import settings
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Client for interacting with Supabase database."""
    
    def __init__(self):
        """Initialize Supabase client."""
        try:
            self.client: Client = create_client(settings.supabase_url, settings.supabase_key)
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.client = None
    
    async def get_menu_info(self, restaurant_id: str) -> Optional[Dict[str, Any]]:
        """Get menu information from database."""
        if not self.client:
            return None
        
        try:
            response = (
                self.client.table("menus")
                .select("id,restaurant_id,name,created_at,updated_at")
                .eq("restaurant_id", restaurant_id)
                .single()
                .execute()
            )
            return response.data if response.data else None
        except Exception as e:
            logger.error(f"Error fetching menu info: {e}")
            return None
    
    async def get_restaurant_info(self, restaurant_id: str) -> Optional[Dict[str, Any]]:
        """Get restaurant information from database."""
        if not self.client:
            return None
        
        try:
            response = (
                self.client.table("restaurants")
                .select("id,name,address,city,country,created_at")
                .eq("id", restaurant_id)
                .single()
                .execute()
            )
            return response.data if response.data else None
        except Exception as e:
            logger.error(f"Error fetching restaurant info: {e}")
            return None
    
    async def save_ocr_result(self, image_url: str, result: Dict[str, Any], user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Save OCR result to database with enhanced metadata support."""
        if not self.client:
            return False
        
        try:
            # Prepare enhanced OCR result data
            enhanced_data = {
                "image_url": image_url,
                "result": result,
                "processed_at": "now()",
                "method": result.get("method", "unknown"),
                "processing_time_ms": result.get("processing_time_ms", 0),
                "enhanced": result.get("enhanced", False),
                "raw_text": result.get("raw_text", ""),
                "menu_items_count": len(result.get("menu_items", []))
            }
            
            # Add user_id if provided
            if user_id:
                enhanced_data["user_id"] = user_id
            
            # Add metadata if provided
            if metadata:
                enhanced_data["metadata"] = metadata
            
            response = self.client.table("ocr_results").insert(enhanced_data).execute()
            logger.info(f"Enhanced OCR result saved: {enhanced_data['menu_items_count']} items, method: {enhanced_data['method']}")
            return True
        except Exception as e:
            logger.error(f"Error saving enhanced OCR result: {e}")
            return False
    
    async def upload_image(self, image_data: bytes, filename: str) -> Optional[str]:
        """Upload image to Supabase storage."""
        if not self.client:
            return None
        
        try:
            response = self.client.storage.from_(settings.supabase_bucket).upload(
                filename,
                image_data,
                file_options={"content-type": "image/jpeg"}
            )
            return self._get_public_url(filename)
        except Exception as e:
            logger.error(f"Error uploading image: {e}")
            return None
    
    def _get_public_url(self, filename: str) -> str:
        """Get public URL for uploaded file."""
        return f"{settings.supabase_url}/storage/v1/object/public/{settings.supabase_bucket}/{filename}"
    
    async def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get OCR processing history."""
        if not self.client:
            return []
        
        try:
            limit = max(1, min(limit, 50))
            response = (
                self.client.table("ocr_results")
                .select("id,user_id,image_url,menu_items_count,method,processing_time_ms,created_at")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error fetching history: {e}")
            return []


# Global instance
_supabase_client = None

def get_supabase_client():
    """Get or create Supabase client instance."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client
