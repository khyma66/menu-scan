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
            response = self.client.table("menus").select("*").eq("restaurant_id", restaurant_id).single().execute()
            return response.data if response.data else None
        except Exception as e:
            logger.error(f"Error fetching menu info: {e}")
            return None
    
    async def get_restaurant_info(self, restaurant_id: str) -> Optional[Dict[str, Any]]:
        """Get restaurant information from database."""
        if not self.client:
            return None
        
        try:
            response = self.client.table("restaurants").select("*").eq("id", restaurant_id).single().execute()
            return response.data if response.data else None
        except Exception as e:
            logger.error(f"Error fetching restaurant info: {e}")
            return None
    
    async def save_ocr_result(self, image_url: str, result: Dict[str, Any]) -> bool:
        """Save OCR result to database."""
        if not self.client:
            return False
        
        try:
            response = self.client.table("ocr_results").insert({
                "image_url": image_url,
                "result": result,
                "created_at": "now()"
            }).execute()
            return True
        except Exception as e:
            logger.error(f"Error saving OCR result: {e}")
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
            response = self.client.table("ocr_results").select("*").order("created_at", desc=True).limit(limit).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error fetching history: {e}")
            return []

