import redis 
from typing import Final

REDIS_URL: Final[str] = "localhost"
REDIS_PORT: Final[int] = 6379
DEFAULT_TTL: Final[int] = 60


class RedisClient:
    def __init__(self, host: str = REDIS_URL, port: int = REDIS_PORT) -> None:
        self.client = redis.Redis(host=host, port=port, decode_responses=True)
    
    def set(self, key: str, value: str) -> None:
        self.client.set(key, value)
    
    def get(self, key: str) -> str|None:
        return self.client.get(key)
    
    def setex(self, key: str, value: str, ttl: int = DEFAULT_TTL) -> None:
        self.client.setex(key, ttl, value)
    
    def delete(self, key: str) -> None:
        self.client.delete(key)
    
    def exists(self, key: str) -> bool:
        return self.client.exists(key)
    
    def keys(self, pattern: str) -> list[str]:
        return self.client.keys(pattern)
    
    def flushdb(self) -> None:
        self.client.flushdb()
    
    def close(self) -> None:
        self.client.close()
    
    def __enter__(self) -> "RedisClient":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool|None:
        self.close()
        return None 

if __name__ == "__main__":
    with RedisClient() as r:
        r.set("mykey", "myvalue")
        print(r.get("mykey"))
        r.setex("temp_key", "I will disappear in 60 seconds", DEFAULT_TTL)
        print(r.get("temp_key"))