import json
import redis
from typing import Final
from models import AgentName, CompletionEvent
from keys import RedisSchema


REDIS_HOST: Final[str] = "localhost"
REDIS_PORT: Final[int] = 6379


class RedisClient:
    """
    Shared Redis client for all agents and the Orchestrator.
    Handles JSON serialisation, key schema, and Pub/Sub.
    """

    def __init__(self, host: str = REDIS_HOST, port: int = REDIS_PORT) -> None:
        self.client = redis.Redis(host=host, port=port, decode_responses=True)

    # ── BASIC ────────────────────────────────────────────

    def set_json(self, key: str, value: dict, ttl: int | None = None) -> None:
        """Serialises a dict and stores it in Redis with optional TTL."""

        serialised = json.dumps(value)
        if ttl:
            self.client.setex(key, ttl, serialised)
        else:
            self.client.set(key, serialised)

    def get_json(self, key: str) -> dict | None:
        """Retrieves a JSON string from Redis and deserialises it."""

        raw: str | None = self.client.get(key)
        return json.loads(raw) if raw else None

    def exists(self, key: str) -> bool:
        """Returns True if the key exists in Redis."""
        return bool(self.client.exists(key))

    def delete(self, key: str) -> None:
        """Deletes a key from Redis."""

        self.client.delete(key)

    # ── BUFFER ───────────────────────────────────────────

    def pop_from_buffer(self, key: str) -> dict | None:
        """
        Pops the next item from a Redis List buffer.
        Used by Ingestion Tool to read from telemetry buffer.
        rpop = pop from right (oldest item first — FIFO order).
        """

        raw: str | None = self.client.rpop(key)
        return json.loads(raw) if raw else None

    def buffer_length(self, key: str) -> int:
        """Returns how many items are waiting in the buffer."""

        return self.client.llen(key)

    # ── TRIP CONTEXT ─────────────────────────────────────

    def store_trip_context(self, trip_id: str, context: dict) -> None:
        """
        Orchestrator calls this to warm the cache at job start.
        Agents read from this key when they hydrate.
        """

        key = RedisSchema.Trip.context(trip_id)
        self.set_json(key, context, ttl=RedisSchema.Trip.CONTEXT_TTL)

    def get_trip_context(self, trip_id: str) -> dict | None:
        """
        Agents call this to hydrate context on task pickup.
        Returns None if context expired or was never loaded.
        """

        key = RedisSchema.Trip.context(trip_id)
        return self.get_json(key)

    # ── AGENT OUTPUT ─────────────────────────────────────

    def store_agent_output(self, trip_id: str, agent: AgentName, output: dict) -> None:
        """
        Agents call this to write their result back to Redis.
        Orchestrator reads this after receiving completion event.
        """
        key = RedisSchema.Trip.output(trip_id, agent)
        self.set_json(key, output, ttl=RedisSchema.Trip.OUTPUT_TTL)

    def get_agent_output(self, trip_id: str, agent: AgentName) -> dict | None:
        """Orchestrator calls this to read an agent result."""

        key = RedisSchema.Trip.output(trip_id, agent)
        return self.get_json(key)

    # ── PUB/SUB ──────────────────────────────────────────

    def publish_completion(self, trip_id: str, event: CompletionEvent) -> None:
        """
        Agents call this when done.
        Publishes to Pub/Sub AND persists to list as fallback.
        """
        channel = RedisSchema.Trip.events_channel(trip_id)
        event_json = event.model_dump_json()
        self.client.publish(channel, event_json)
        self.client.lpush(channel, event_json)
        self.client.expire(channel, RedisSchema.Trip.EVENT_TTL)

    def subscribe_to_trip(self, trip_id: str):
        """
        Orchestrator calls this to listen for agent completion events.
        Returns a pubsub object to iterate over.
        """
        channel = RedisSchema.Trip.events_channel(trip_id)
        pubsub = self.client.pubsub()
        pubsub.subscribe(channel)
        return pubsub

    # ── LIFECYCLE ────────────────────────────────────────

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "RedisClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
