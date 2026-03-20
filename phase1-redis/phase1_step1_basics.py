import redis 
import json
from typing import Final, Optional

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

if __name__ == "__main__":
    # The 'with' statement handles the connection lifecycle for us.
    print("--- Redis Basics Workshop ---")
    
    with RedisClient() as r:
        # 1. Basic Set/Get
        print("\n[Step 1] Setting a persistent key...")
        r.set("workshop:name", "Exploring Redis")
        name = r.get("workshop:name")
        print(f"Retrieved Value: {name}")

        # 2. Expiration (TTL)
        print("\n[Step 2] Setting a temporary key (TTL=60s)...")
        r.setex("workshop:temp", "I will vanish soon", DEFAULT_TTL)
        temp_val = r.get("workshop:temp")
        print(f"Retrieved Temp Value: {temp_val}")

        # 3. Checking Existence
        if r.exists("workshop:name"):
            print("\n[Step 3] 'workshop:name' successfully verified in Redis.")

        # 4. JSON Serialization
        print("\n[Step 4] Testing JSON serialization...")
        user_data = {"id": 1, "name": "Agentic User", "role": "Architect"}
        r.set_json("workshop:user:1", user_data)
        retrieved_user = r.get_json("workshop:user:1")
        print(f"Retrieved JSON Data: {retrieved_user}")
        if retrieved_user == user_data:
            print("Successfully verified JSON serialization integrity.")
            
    print("\n[Done] Connection closed automatically by the Context Manager.")