import json
from models import TelemetryPacket, TripEvent, Priority
from redis_client import RedisClient
from keys import RedisSchema


# ── PRIORITY MAP ─────────────────────────────────────────
# maps raw priority string from device → Priority enum
PRIORITY_MAP: dict[str, Priority] = {
    "critical": Priority.CRITICAL,
    "high": Priority.HIGH,
    "medium": Priority.MEDIUM,
    "low": Priority.LOW,
}


def ingest_next_event(client: RedisClient, device_id: str) -> TripEvent | None:
    """
    Pops the next raw event from the telemetry buffer,
    validates it, transforms it into a TripEvent,
    and returns it to the Orchestrator.

    Returns None if the buffer is empty.
    """

    # ── STEP 1: POP FROM BUFFER ──────────────────────────
    key = RedisSchema.Telemetry.buffer(device_id)
    raw: dict | None = client.pop_from_buffer(key)

    if raw is None:
        print(f"[Ingestion] buffer empty for {device_id}")
        return None

    print(f"[Ingestion] popped raw event from buffer")

    # ── STEP 2: VALIDATE ─────────────────────────────────
    # Pydantic raises immediately if packet is malformed
    packet = TelemetryPacket(**raw)
    print(f"[Ingestion] validated → {packet.batch_id}")

    # ── STEP 3: PERSIST TO POSTGRES ──────────────────────
    # TODO: write raw packet to Postgres events table
    print(f"[Ingestion] (stub) persisting to Postgres...")

    # ── STEP 4: TRANSFORM → TripEvent ────────────────────
    priority_str: str = packet.event.priority.lower()
    priority: Priority = PRIORITY_MAP.get(priority_str, Priority.LOW)

    # build flat TripEvent from nested TelemetryPacket
    trip_event = TripEvent(
        batch_id=packet.batch_id,
        trip_id=packet.event.trip_id,
        driver_id=packet.event.driver_id,
        truck_id=packet.event.truck_id,
        timestamp=packet.event.timestamp,
        event_type=packet.event.event_type,
        category=packet.event.category,
        priority=priority,
        is_emergency=packet.is_emergency,
        location=packet.event.location,
        details=packet.event.details,
        evidence=packet.evidence,
    )

    print(f"[Ingestion] transformed → {trip_event.event_type} [{priority.name}]")
    return trip_event


if __name__ == "__main__":
    """Quick smoke test — pop one event and print it."""
    print(">>> Ingestion Tool smoke test\n")

    with RedisClient() as r:
        event = ingest_next_event(r, "T12345")

        if event:
            print(f"\n>>> TripEvent produced:")
            print(f"    trip_id    → {event.trip_id}")
            print(f"    event_type → {event.event_type}")
            print(f"    priority   → {event.priority.name}")
            print(f"    emergency  → {event.is_emergency}")
            print(f"    details    → {event.details}")
