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
    Handles JSON serialisation, key schema, Pub/Sub, and
    priority-aware buffer operations.
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

    # ── PRIORITY BUFFER ──────────────────────────────────
    # Uses Redis Sorted Set (ZSet) for priority-aware ordering.
    # Lower score = higher priority = processed first by zpopmin.
    #
    # Priority score mapping:
    #   CRITICAL = 0  → always processed first
    #   HIGH     = 3
    #   MEDIUM   = 6
    #   LOW      = 9  → processed last

    def push_to_buffer(self, key: str, payload: str, priority: int) -> None:
        """
        Pushes an event to the priority buffer.
        Uses zadd — lower score = higher priority.

        Args:
            key:      Redis key for the buffer (from RedisSchema)
            payload:  JSON string of the TelemetryPacket
            priority: Priority score (0=CRITICAL, 3=HIGH, 6=MEDIUM, 9=LOW)
        """
        self.client.zadd(key, {payload: priority})

    def pop_from_buffer(self, key: str) -> dict | None:
        """
        Pops the highest priority event from the buffer.
        zpopmin = pop member with lowest score = highest priority first.

        Returns None if the buffer is empty.
        """
        result = self.client.zpopmin(key, count=1)
        if not result:
            return None
        raw_json, score = result[0]
        return json.loads(raw_json)

    def buffer_length(self, key: str) -> int:
        """Returns how many events are waiting in the buffer."""
        # zcard for Sorted Sets — equivalent of llen for Lists
        return self.client.zcard(key)

    def peek_buffer(self, key: str, count: int = 5) -> list[dict]:
        """
        Peeks at the top N events without removing them.
        Useful for debugging — see what is queued without consuming.
        """
        results = self.client.zrange(key, 0, count - 1, withscores=True)
        return [
            {"event": json.loads(raw), "priority_score": score}
            for raw, score in results
        ]

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
        Returns None if context has expired or was never loaded.
        """
        key = RedisSchema.Trip.context(trip_id)
        return self.get_json(key)

    # ── AGENT OUTPUT ─────────────────────────────────────

    def store_agent_output(self, trip_id: str, agent: AgentName, output: dict) -> None:
        """
        Agents call this to write their result back to Redis.
        Orchestrator reads this after receiving the completion event.
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
        Publishes to Pub/Sub AND persists to list as durable fallback.
        If Orchestrator misses the Pub/Sub message it can replay from list.
        """
        channel = RedisSchema.Trip.events_channel(trip_id)
        event_json = event.model_dump_json()

        # fire-and-forget Pub/Sub signal
        self.client.publish(channel, event_json)

        # durable fallback — persists for EVENT_TTL seconds
        self.client.lpush(channel, event_json)
        self.client.expire(channel, RedisSchema.Trip.EVENT_TTL)

    def subscribe_to_trip(self, trip_id: str):
        """
        Orchestrator calls this to listen for agent completion events.
        Returns a pubsub object to iterate over.

        Note: subscriber must use a SEPARATE RedisClient instance
        from any publisher — a subscribed connection cannot send
        regular commands.
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
