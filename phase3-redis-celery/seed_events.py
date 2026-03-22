from redis_client import RedisClient
from keys import RedisSchema
from models import (
    TelemetryPacket,
    Priority,
    EVENT_MATRIX,
)


# ── PRIORITY MAP ─────────────────────────────────────────
# maps priority string from EVENT_MATRIX → Priority enum score
# used for Redis Sorted Set scoring

PRIORITY_MAP: dict[str, Priority] = {
    "critical": Priority.CRITICAL,
    "high": Priority.HIGH,
    "medium": Priority.MEDIUM,
    "low": Priority.LOW,
}


# ── SEED EVENTS ──────────────────────────────────────────
# Six events covering all sources, ping types, and priority levels.
# All event_types match EVENT_MATRIX keys exactly.
# All device events carry spatio-temporal anchor fields.

EVENTS: list[dict] = [
    # 1. DEVICE — Emergency Ping — collision — CRITICAL
    {
        "batch_id": "EMERGENCY-T12345-2026-03-07-08-44-23",
        "ping_type": "emergency",
        "source": "telematics_device",
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
            "trip_meter_km": 34.2,
            "odometer_km": 180234.2,
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
    # 2. DRIVER — SOS from driver app — CRITICAL
    {
        "batch_id": "DRIVER-SOS-D6789-2026-03-07-09-00-00",
        "ping_type": "emergency",
        "source": "driver_app",
        "is_emergency": True,
        "event": {
            "event_id": "EV-SOS-D6789-001",
            "device_event_id": "APP-001",
            "trip_id": "TRIP-T12345-2026-03-07-08:00",
            "driver_id": "D6789",
            "truck_id": "T12345",
            "event_type": "driver_sos",
            "category": "critical",
            "priority": "critical",
            "timestamp": "2026-03-07T09:00:00Z",
            "offset_seconds": None,
            "trip_meter_km": None,
            "odometer_km": None,
            "location": {"lat": 1.2900, "lon": 104.0200},
            "details": {
                "message": "Need immediate assistance",
            },
        },
        "evidence": None,
    },
    # 3. DEVICE — High-Speed Send — harsh_brake — HIGH
    {
        "batch_id": "HIGH-T12345-2026-03-07-09-10-00",
        "ping_type": "high_speed",
        "source": "telematics_device",
        "is_emergency": False,
        "event": {
            "event_id": "EV-HIGH-T12345-002",
            "device_event_id": "DEV-002",
            "trip_id": "TRIP-T12345-2026-03-07-08:00",
            "driver_id": "D6789",
            "truck_id": "T12345",
            "event_type": "harsh_brake",
            "category": "harsh_events",
            "priority": "high",
            "timestamp": "2026-03-07T09:10:00Z",
            "offset_seconds": 4200,
            "trip_meter_km": 48.7,
            "odometer_km": 180248.7,
            "location": {"lat": 1.3000, "lon": 103.8500},
            "details": {
                "g_force_x": -0.92,
                "speed_kmh": 88,
                "confidence": 0.95,
                "duration_seconds": 2,
            },
        },
        "evidence": None,
    },
    # 4. DRIVER — dispute — HIGH
    {
        "batch_id": "DRIVER-DISPUTE-D6789-2026-03-07-09-30-00",
        "ping_type": "high_speed",
        "source": "driver_app",
        "is_emergency": False,
        "event": {
            "event_id": "EV-DISPUTE-D6789-001",
            "device_event_id": "APP-002",
            "trip_id": "TRIP-T12345-2026-03-07-08:00",
            "driver_id": "D6789",
            "truck_id": "T12345",
            "event_type": "driver_dispute",
            "category": "driver_feedback",
            "priority": "high",
            "timestamp": "2026-03-07T09:30:00Z",
            "offset_seconds": None,
            "trip_meter_km": None,
            "odometer_km": None,
            "location": None,
            "details": {
                "disputed_event_id": "EV-HIGH-T12345-002",
                "reason": "Road conditions caused braking, not driver error",
            },
        },
        "evidence": None,
    },
    # 5. DEVICE — Medium-Speed Send — speeding — MEDIUM
    {
        "batch_id": "MEDIUM-T12345-2026-03-07-10-00-00",
        "ping_type": "medium_speed",
        "source": "telematics_device",
        "is_emergency": False,
        "event": {
            "event_id": "EV-MEDIUM-T12345-003",
            "device_event_id": "DEV-003",
            "trip_id": "TRIP-T12345-2026-03-07-08:00",
            "driver_id": "D6789",
            "truck_id": "T12345",
            "event_type": "speeding",
            "category": "speed_compliance",
            "priority": "medium",
            "timestamp": "2026-03-07T10:00:00Z",
            "offset_seconds": 7200,
            "trip_meter_km": 62.4,
            "odometer_km": 180262.4,
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
    # 6. DEVICE — 10-Min Batch Ping — smoothness_log — LOW
    {
        "batch_id": "BATCH-T12345-2026-03-07-10-10-00",
        "ping_type": "batch",
        "source": "telematics_device",
        "is_emergency": False,
        "event": {
            "event_id": "EV-SMOOTH-T12345-001",
            "device_event_id": "DEV-004",
            "trip_id": "TRIP-T12345-2026-03-07-08:00",
            "driver_id": "D6789",
            "truck_id": "T12345",
            "event_type": "smoothness_log",
            "category": "normal_operation",
            "priority": "low",
            "timestamp": "2026-03-07T10:10:00Z",
            "offset_seconds": 7800,
            "trip_meter_km": 68.1,
            "odometer_km": 180268.1,
            "location": {"lat": 1.3250, "lon": 103.8750},
            "details": {
                "sample_count": 600,
                "window_seconds": 600,
                "speed": {
                    "mean_kmh": 72.3,
                    "std_dev": 8.1,
                    "max_kmh": 94.0,
                    "variance": 65.6,
                },
                "longitudinal": {
                    "mean_accel_g": 0.04,
                    "std_dev": 0.12,
                    "max_decel_g": -0.31,
                    "harsh_brake_count": 0,
                    "harsh_accel_count": 0,
                },
                "lateral": {
                    "mean_lateral_g": 0.02,
                    "max_lateral_g": 0.18,
                    "harsh_corner_count": 0,
                },
                "jerk": {
                    "mean": 0.008,
                    "max": 0.041,
                    "std_dev": 0.006,
                },
                "engine": {
                    "mean_rpm": 1820,
                    "max_rpm": 2340,
                    "idle_seconds": 45,
                    "idle_events": 1,
                    "longest_idle_seconds": 38,
                    "over_rev_count": 0,
                    "over_rev_seconds": 0,
                },
                "incident_event_ids": ["DEV-002", "DEV-003"],
                "raw_log_url": "s3://tracedata-sensors/T12345-batch-001.bin",
            },
        },
        "evidence": None,
    },
]


def seed_events(client: RedisClient) -> None:
    """
    Validates each event as a TelemetryPacket and pushes
    to the Redis priority buffer (Sorted Set).
    Priority score read from EVENT_MATRIX — not from raw event string.
    Higher priority events will be popped first by Ingestion Tool.
    """
    for raw in EVENTS:
        packet = TelemetryPacket(**raw)
        device_id = packet.event.truck_id
        key = RedisSchema.Telemetry.buffer(device_id)

        # read priority from EVENT_MATRIX — source of truth
        # overrides whatever the device stamped
        event_type = packet.event.event_type
        priority_str = EVENT_MATRIX[event_type].priority
        priority_score = int(PRIORITY_MAP[priority_str])

        # zadd — lower score = higher priority = popped first by zpopmin
        client.push_to_buffer(key, packet.model_dump_json(), priority_score)

        print(f"  seeded → {packet.batch_id}")
        print(f"           source:     {packet.source.value}")
        print(f"           event_type: {event_type} [{priority_str}]")
        print(f"           score:      {priority_score}\n")


if __name__ == "__main__":
    print(">>> Seeding events into Redis priority buffer...\n")

    with RedisClient() as r:
        seed_events(r)

    print(">>> Done. Check Redis Insight → telemetry:T12345:buffer")
