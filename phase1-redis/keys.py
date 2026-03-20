from typing import Final

# ── TTL CONSTANTS ───────────────────────────────────────
TRIP_CONTEXT_TTL: Final[int] = 7200          # 2 hours — active trip window
AGENT_OUTPUT_TTL: Final[int] = 3600          # 1 hour — enough for Orchestrator to read
DRIVER_PROFILE_TTL: Final[int] = 86400       # 24 hours — driver snapshot cache

# ── KEY BUILDERS ────────────────────────────────────────
# These are functions, not plain strings.
# Why? So no agent ever hardcodes "trip:123:context" by hand.
# One change here fixes every agent at once.

def trip_context_key(trip_id: str) -> str:
    """Full trip context loaded by Orchestrator at job start."""
    return f"trip:{trip_id}:context"

def trip_output_key(trip_id: str, agent: str) -> str:
    """Output written by a specific agent for a trip."""
    return f"trip:{trip_id}:{agent}_output"

def trip_events_channel(trip_id: str) -> str:
    """Redis Pub/Sub channel for a trip — agents publish completion here."""
    return f"trip:{trip_id}:events"

def driver_profile_key(driver_id: str) -> str:
    """Driver history snapshot — loaded once per job, shared across agents."""
    return f"driver:{driver_id}:profile"

def telemetry_buffer_key(device_id: str) -> str:
    """Raw telemetry aggregation buffer — Kafka stand-in for now."""
    return f"telemetry:{device_id}:buffer"