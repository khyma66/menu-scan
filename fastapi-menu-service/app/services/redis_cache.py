"""Redis cache service for caching OCR results."""

import json
import hashlib
from typing import Optional, Any
from app.config import settings
import redis.asyncio as redis
from datetime import timedelta


class RedisCache:
    """Redis cache service for storing and retrieving cached data."""
    
    def __init__(self):
        """Initialize Redis connection."""
        self.redis_client: Optional[redis.Redis] = None
        self._connection_pool = None
        self._enabled = True  # Will be set to False if connection fails
    
    async def connect(self):
        """Create Redis connection pool."""
        if not self._enabled:
            return
        
        if self._connection_pool is None:
            try:
                self._connection_pool = redis.ConnectionPool(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    db=settings.redis_db,
                    password=settings.redis_password,
                    decode_responses=True,
                    socket_connect_timeout=2,  # Quick timeout
                    socket_timeout=2,
                )
                self.redis_client = redis.Redis(connection_pool=self._connection_pool)
            except Exception:
                # If connection fails, disable Redis for this session
                self._enabled = False
                self.redis_client = None
                self._connection_pool = None
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
        if self._connection_pool:
            self._connection_pool.disconnect()
            self._connection_pool = None
    
    async def ping(self):
        """Ping Redis server to check connection."""
        if not self._enabled:
            raise Exception("Redis is disabled (connection unavailable)")
        
        try:
            if not self.redis_client:
                await self.connect()
            if not self.redis_client:
                raise Exception("Redis connection unavailable")
            return await self.redis_client.ping()
        except Exception:
            self._enabled = False
            raise
    
    def _generate_key(self, image_url: str) -> str:
        """Generate cache key from image URL."""
        return f"ocr:{hashlib.md5(image_url.encode()).hexdigest()}"
    
    async def get(self, image_url: str) -> Optional[dict]:
        """Retrieve cached data for an image URL."""
        if not self._enabled:
            return None
        
        try:
            if not self.redis_client:
                await self.connect()
            if not self.redis_client:
                return None
            
            key = self._generate_key(image_url)
            cached_data = await self.redis_client.get(key)
            
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception:
            self._enabled = False
            return None
    
    async def set(self, image_url: str, data: dict, ttl: int = settings.redis_ttl):
        """Cache data for an image URL."""
        if not self._enabled:
            return  # Silently skip if Redis unavailable
        
        try:
            if not self.redis_client:
                await self.connect()
            if not self.redis_client:
                return
            
            key = self._generate_key(image_url)
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(data)
            )
        except Exception:
            self._enabled = False
            # Silently fail - caching is optional
    
    async def delete(self, image_url: str):
        """Delete cached data for an image URL."""
        if not self.redis_client:
            await self.connect()
        
        key = self._generate_key(image_url)
        await self.redis_client.delete(key)
    
    async def exists(self, image_url: str) -> bool:
        """Check if cached data exists for an image URL."""
        if not self.redis_client:
            await self.connect()
        
        key = self._generate_key(image_url)
        return await self.redis_client.exists(key) > 0

