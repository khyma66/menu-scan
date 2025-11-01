"""Authentication service for Supabase auth."""

from supabase import create_client, Client
from app.config import settings
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Service for handling user authentication."""
    
    def __init__(self):
        """Initialize Supabase auth client."""
        try:
            self.supabase: Client = create_client(settings.supabase_url, settings.supabase_key)
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.supabase = None
    
    async def sign_in_with_google(self) -> Dict[str, Any]:
        """
        Initialize Google sign-in.
        
        Returns:
            Sign-in URL for frontend to redirect to
        """
        if not self.supabase:
            raise Exception("Supabase client not initialized")
        
        try:
            # This would be handled by frontend redirect
            # Backend provides auth state
            response = self.supabase.auth.sign_in_with_oauth({
                "provider": "google",
                "options": {
                    "redirect_to": f"{settings.api_url}/auth/callback"
                }
            })
            return response
        except Exception as e:
            logger.error(f"Error signing in with Google: {e}")
            raise
    
    async def get_user(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user from access token.
        
        Args:
            access_token: JWT access token
            
        Returns:
            User data or None
        """
        if not self.supabase:
            return None
        
        try:
            user = self.supabase.auth.get_user(access_token)
            return user.user.model_dump() if user else None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token.
        
        Args:
            token: JWT token to verify
            
        Returns:
            Decoded token payload or None
        """
        if not self.supabase:
            return None
        
        try:
            # Set the session with the token
            self.supabase.auth.set_session(token)
            response = self.supabase.auth.get_session()
            
            if response.session and response.session.user:
                return response.session.user.model_dump()
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None
    
    async def create_user_profile(self, user_id: str, email: str, full_name: Optional[str] = None) -> bool:
        """
        Create user profile in database.
        
        Args:
            user_id: Supabase user ID
            email: User email
            full_name: User's full name
            
        Returns:
            True if successful
        """
        if not self.supabase:
            return False
        
        try:
            response = self.supabase.table("users").insert({
                "id": user_id,
                "email": email,
                "full_name": full_name,
            }).execute()
            return True
        except Exception as e:
            logger.error(f"Error creating user profile: {e}")
            return False
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile from database.
        
        Args:
            user_id: User ID
            
        Returns:
            User profile or None
        """
        if not self.supabase:
            return None
        
        try:
            response = self.supabase.table("users").select("*").eq("id", user_id).single().execute()
            return response.data if response.data else None
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    async def update_user_profile(self, user_id: str, data: Dict[str, Any]) -> bool:
        """
        Update user profile.
        
        Args:
            user_id: User ID
            data: Profile data to update
            
        Returns:
            True if successful
        """
        if not self.supabase:
            return False
        
        try:
            response = self.supabase.table("users").update(data).eq("id", user_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return False

