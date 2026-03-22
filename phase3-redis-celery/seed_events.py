import json
from datetime import datetime
from redis_client import RedisClient
from keys import RedisSchema
from models import TelemetryPacket, TelemetryEvent, Evidence, Location


EVENTS: list[dict] = [
    {
        "batch_id": "EMERGENCY-T12345-2026-03-07-08-44-23",
        "is_emergency": True,
        "event": {
            "event_id": "EV-EMERGENCY-T12345-001",
            "device_event_id": "DEV-001",
            "trip_id": "TRIP-T12345-2026-03-07-08:00",
            "driver_id": "D6789",
            "truck_id": "T12345",
            "event_type": "collision",
            "category": "critical",
            "priority": "critical",
            "timestamp": "2026-03-07T08:44:23Z",
            "offset_seconds": 2963,
            "location": {"lat": 1.2863, "lon": 104.0115},
            "details": {
                "g_force_magnitude": 2.3,
                "confidence": 0.99,
                "airbag_triggered": True,
                "impact_direction": "front_left",
                "speed_kmh": 48,
                "injury_severity_estimate": "moderate",
            },
        },
        "evidence": {
            "video_url": "s3://tracedata-clips/EMERGENCY-T12345.mp4",
            "video_duration_seconds": 10,
            "voice_url": "s3://tracedata-voice/EMERGENCY-T12345.wav",
            "voice_duration_seconds": 30,
            "sensor_dump_url": "s3://tracedata-sensors/EMERGENCY-T12345.bin",
            "sensor_dump_size_bytes": 5242880,
        },
    },
    {
        "batch_id": "HIGH-T12345-2026-03-07-09-10-00",
        "is_emergency": False,
        "event": {
            "event_id": "EV-HIGH-T12345-002",
            "device_event_id": "DEV-002",
            "trip_id": "TRIP-T12345-2026-03-07-08:00",
            "driver_id": "D6789",
            "truck_id": "T12345",
            "event_type": "harsh_braking",
            "category": "high",
            "priority": "high",
            "timestamp": "2026-03-07T09:10:00Z",
            "offset_seconds": 4200,
            "location": {"lat": 1.3000, "lon": 103.8500},
            "details": {
                "deceleration_g": 0.8,
                "speed_before_kmh": 92,
                "speed_after_kmh": 41,
                "confidence": 0.95,
            },
        },
        "evidence": None,
    },
    {
        "batch_id": "MEDIUM-T12345-2026-03-07-10-00-00",
        "is_emergency": False,
        "event": {
            "event_id": "EV-MEDIUM-T12345-003",
            "device_event_id": "DEV-003",
            "trip_id": "TRIP-T12345-2026-03-07-08:00",
            "driver_id": "D6789",
            "truck_id": "T12345",
            "event_type": "overspeed",
            "category": "medium",
            "priority": "medium",
            "timestamp": "2026-03-07T10:00:00Z",
            "offset_seconds": 7200,
            "location": {"lat": 1.3200, "lon": 103.8700},
            "details": {
                "speed_kmh": 112,
                "speed_limit_kmh": 90,
                "duration_seconds": 45,
                "confidence": 0.97,
            },
        },
        "evidence": None,
    },
]


def seed_events(client: RedisClient) -> None:
    """
    Validates each event as a TelemetryPacket
    and pushes to the Redis telemetry buffer.
    """
    for raw in EVENTS:
        packet = TelemetryPacket(**raw)  #  validate via Pydantic
        device_id = packet.event.truck_id
        key = RedisSchema.Telemetry.buffer(device_id)

        #  push to Redis list — lpush means newest event at the front
        client.client.lpush(key, packet.model_dump_json())

        print(f"  seeded → {packet.batch_id} [{packet.event.priority}]")


if __name__ == "__main__":
    print(">>> Seeding telemetry events into Redis buffer...\n")

    with RedisClient() as r:
        seed_events(r)

    print("\n>>> Done. Redis buffer ready for ingestion.")
