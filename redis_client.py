"""
Redis client for caching and session management.
"""
import json
from typing import Any, Optional

import redis.asyncio as redis

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class RedisClient:
    """Async Redis client wrapper."""
    
    def __init__(self):
        self._client: Optional[redis.Redis] = None
    
    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self._client = redis.from_url(
                str(settings.REDIS_URL),
                decode_responses=True,
            )
            await self._client.ping()
            logger.info("redis_connected")
        except Exception as e:
            logger.error("redis_connection_failed", error=str(e))
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._client:
            await self._client.close()
            logger.info("redis_disconnected")
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        if not self._client:
            return None
        return await self._client.get(key)
    
    async def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value by key."""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None
    
    async def set(
        self,
        key: str,
        value: str,
        expire: Optional[int] = None,
    ) -> bool:
        """Set value with optional expiration (seconds)."""
        if not self._client:
            return False
        return await self._client.set(key, value, ex=expire)
    
    async def set_json(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None,
    ) -> bool:
        """Set JSON value with optional expiration."""
        return await self.set(key, json.dumps(value), expire)
    
    async def delete(self, key: str) -> int:
        """Delete key(s)."""
        if not self._client:
            return 0
        return await self._client.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        if not self._client:
            return False
        return await self._client.exists(key) > 0
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on key."""
        if not self._client:
            return False
        return await self._client.expire(key, seconds)
    
    async def ttl(self, key: str) -> int:
        """Get time to live for key."""
        if not self._client:
            return -2
        return await self._client.ttl(key)
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment value by amount."""
        if not self._client:
            return 0
        return await self._client.incrby(key, amount)
    
    async def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement value by amount."""
        if not self._client:
            return 0
        return await self._client.decrby(key, amount)
    
    # Session Management
    async def set_session(
        self,
        session_id: str,
        data: dict,
        expire: int = 3600,
    ) -> bool:
        """Set session data."""
        key = f"session:{session_id}"
        return await self.set_json(key, data, expire)
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get session data."""
        key = f"session:{session_id}"
        return await self.get_json(key)
    
    async def delete_session(self, session_id: str) -> int:
        """Delete session."""
        key = f"session:{session_id}"
        return await self.delete(key)
    
    # Caching
    async def cache_get(self, cache_key: str) -> Optional[Any]:
        """Get cached value."""
        key = f"cache:{cache_key}"
        return await self.get_json(key)
    
    async def cache_set(
        self,
        cache_key: str,
        value: Any,
        expire: int = 300,
    ) -> bool:
        """Set cached value."""
        key = f"cache:{cache_key}"
        return await self.set_json(key, value, expire)
    
    async def cache_delete(self, cache_key: str) -> int:
        """Delete cached value."""
        key = f"cache:{cache_key}"
        return await self.delete(key)
    
    # Rate Limiting (Sliding Window)
    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> tuple[bool, int, int]:
        """
        Check rate limit using sliding window.
        Returns: (allowed, remaining, reset_after)
        """
        if not self._client:
            return True, max_requests, 0
        
        current_key = f"ratelimit:{key}:{window_seconds}"
        now = await self._client.time()
        current_time = int(now[0])
        window_start = current_time - window_seconds
        
        # Remove old entries
        await self._client.zremrangebyscore(current_key, 0, window_start)
        
        # Count current requests
        current_count = await self._client.zcard(current_key)
        
        if current_count >= max_requests:
            # Get oldest entry for reset time
            oldest = await self._client.zrange(current_key, 0, 0, withscores=True)
            reset_after = int(oldest[0][1]) + window_seconds - current_time if oldest else window_seconds
            return False, 0, max(0, reset_after)
        
        # Add current request
        await self._client.zadd(current_key, {str(current_time): current_time})
        await self._client.expire(current_key, window_seconds)
        
        remaining = max_requests - current_count - 1
        return True, remaining, 0
    
    # Game State Cache
    async def get_game_state(self, user_id: int, game_type: str) -> Optional[dict]:
        """Get cached game state."""
        key = f"game:{user_id}:{game_type}"
        return await self.get_json(key)
    
    async def set_game_state(
        self,
        user_id: int,
        game_type: str,
        state: dict,
        expire: int = 86400,
    ) -> bool:
        """Set cached game state."""
        key = f"game:{user_id}:{game_type}"
        return await self.set_json(key, state, expire)
    
    async def delete_game_state(self, user_id: int, game_type: str) -> int:
        """Delete cached game state."""
        key = f"game:{user_id}:{game_type}"
        return await self.delete(key)
    
    # Pub/Sub for real-time features
    async def publish(self, channel: str, message: str) -> int:
        """Publish message to channel."""
        if not self._client:
            return 0
        return await self._client.publish(channel, message)
    
    async def subscribe(self, channel: str):
        """Subscribe to channel."""
        if not self._client:
            return None
        pubsub = self._client.pubsub()
        await pubsub.subscribe(channel)
        return pubsub


# Global Redis client instance
redis_client = RedisClient()
