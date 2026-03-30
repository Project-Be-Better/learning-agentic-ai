---
name: setup-redis
description: Instructions for using the RedisClient wrapper and following the project's key schema (RedisSchema).
---

# Setup Redis Skill

Use this skill when you need to interact with Redis for caching context, storing agent outputs, or publishing events.

## Core Pattern

Always use the `RedisClient` wrapper and the `RedisSchema` builder to ensure consistency and avoid key collisions.

```python
from phase1_redis.redis_client import RedisClient
from phase1_redis.keys import RedisSchema

# Using the Context Manager (Recommended)
with RedisClient() as r:
    # Build key using Schema
    key = RedisSchema.Trip.context("TRIP-001")
    
    # Store structured data (JSON) with TTL
    data = {"driver_id": "D-123", "status": "active"}
    r.set_json(key, data, ttl=RedisSchema.Trip.CONTEXT_TTL)
    
    # Retrieve data
    cached = r.get_json(key)
```

## Key Naming Conventions (RedisSchema)

| Domain | Purpose | Key Pattern | Data Structure |
|---|---|---|---|
| **Trip** | Full trip context | `trip:{trip_id}:context` | TripContext JSON |
| **Trip** | Agent output | `trip:{trip_id}:{agent}_output` | AgentResult JSON |
| **Trip** | Pub/Sub | `trip:{trip_id}:events` | Pub/Sub Channel |
| **Driver** | Driver profile | `driver:{driver_id}:profile` | DriverProfile JSON |
| **Telemetry** | IoT buffer | `telemetry:{device_id}:buffer` | Redis List |

## TTL Policies

Always set a TTL to ensure Redis stays clean.

- **Trip Context**: 7200 seconds (2 hours)
- **Agent Output**: 3600 seconds (1 hour)
- **Transient Events**: 300 seconds (5 mins)
- **Driver Profile**: 86400 seconds (24 hours)

## JSON Serialization

Always use `set_json()` and `get_json()` when storing complex structures like dictionaries or Pydantic models (use `model_dump()` before storing).

```python
# Storing a Pydantic model
output = AgentResult(...)
r.set_json(key, output.model_dump(), ttl=3600)
```
