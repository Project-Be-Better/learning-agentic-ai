import redis 
import json
from typing import Final

# Redis Connection Defaults
# Using Final[str] indicates these values should not be changed during runtime.
REDIS_HOST: Final[str] = "localhost"
REDIS_PORT: Final[int] = 6379

# Default Time-To-Live (TTL) in seconds. 
# Redis is often used for temporary data; TTL ensures it cleans up after itself.
DEFAULT_TTL: Final[int] = 60


class RedisClient:
    """
    A lightweight wrapper around the redis-py library.
    
    Why use a wrapper?
    1. Focus: It provides only the methods our application needs.
    2. Resilience: We can add global error handling or logging in one place.
    3. Consistency: It ensures all connections use 'decode_responses=True'.
    """

    def __init__(self, host: str = REDIS_HOST, port: int = REDIS_PORT) -> None:
        """
        Initializes the Redis connection.
        
        Args:
            host: The hostname of the Redis server (default: localhost).
            port: The port Redis is listening on (default: 6379).
        """
        # decode_responses=True is CRITICAL. 
        # Without it, Redis returns 'bytes' (e.g., b'value'). 
        # With it, we get Python 'str' (strings).
        self.client = redis.Redis(host=host, port=port, decode_responses=True)
    
    def set(self, key: str, value: str) -> None:
        """
        Sets a key to a specific value in Redis. 
        If the key already exists, it is overwritten.
        """
        self.client.set(key, value)
    
    def get(self, key: str) -> str|None:
        """
        Retrieves the value of a key. 
        Returns None if the key does not exist.
        """
        return self.client.get(key)
    
    def setex(self, key: str, value: str, ttl: int = DEFAULT_TTL) -> None:
        """
        Set-With-Expire: Sets a key with an expiration time.
        Great for session tokens or temporary caches.
        """
        self.client.setex(key, ttl, value)
    
    def delete(self, key: str) -> None:
        """Removes one or more keys from the database."""
        self.client.delete(key)
    
    def exists(self, key: str) -> bool:
        """Returns True if the key exists in Redis, False otherwise."""
        # Note: redis-py returns 1 for True, 0 for False. Consistent with bool().
        return bool(self.client.exists(key))
    
    def keys(self, pattern: str) -> list[str]:
        """
        Returns a list of keys matching a pattern (e.g., 'user:*').
        WARNING: In production, 'keys' can be slow on large datasets. Use 'scan' instead.
        """
        return self.client.keys(pattern)
    
    def flushdb(self) -> None:
        """DANGER: Deletes ALL keys in the current database."""
        self.client.flushdb()
    
    def close(self) -> None:
        """Explicitly closes the connection to the Redis server."""
        self.client.close()
    
    def __enter__(self) -> "RedisClient":
        """
        Part of the 'Context Manager' pattern. 
        Allows usage like: 'with RedisClient() as r:'
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Ensures the connection is closed even if an error occurs.
        This prevents connection leaks in production.
        """
        self.close()

    def set_json(self, key: str, value: dict, ttl: int | None = None) -> None:
        """
        Serializes a Python dictionary to a JSON string and stores it in Redis.
        
        Args:
            key: The Redis key.
            value: The dictionary to store.
            ttl: Optional time-to-live in seconds.
        """
        # We must serialize the dict because Redis only stores strings, bytes, or numbers.
        serialised = json.dumps(value)
        if ttl:
            self.client.setex(key, ttl, serialised)
        else:
            self.client.set(key, serialised)

    def get_json(self, key: str) -> dict | None:
        """
        Retrieves a JSON string from Redis and deserializes it back into a Python dictionary.
        
        Returns:
            The dictionary if the key exists, None otherwise.
        """
        raw: str | None = self.client.get(key)
        # Only attempt to parse if the key actually exists in Redis.
        return json.loads(raw) if raw else None