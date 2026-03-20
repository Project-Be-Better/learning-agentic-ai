from typing import Final, Literal

class RedisSchema:
    """
    Centralized Redis Key Schema for Tracedata
    
    Why this pattern?
    1. Association: TTLs and data descriptions are bundled with the key builder.
    2. Namespace Safety: Prevents accidental string collisions across modules.
    3. Type Safety: Uses Literal to restrict agent and channel inputs.
    """

    class Trip:
        """Domain: Vehicle trips, agent coordination, and results."""
        
        # TTLs (in seconds)
        CONTEXT_TTL: Final[int] = 7200  # 2 hours - active trip window
        OUTPUT_TTL: Final[int] = 3600   # 1 hour - enough for Orchestrator to read
        EVENT_TTL: Final[int] = 300     # 5 mins - transient pub/sub state
        
        @staticmethod
        def context(trip_id: str) -> str:
            """
            Key for the full trip context (Pickup, Destination, Status).
            Data Structure: TripContext JSON.
            """
            return f"trip:{trip_id}:context"

        @staticmethod
        def output(trip_id: str, agent: Literal["safety", "scoring", "sentiment", "coaching", "driver_support"]) -> str:
            """
            Output written by a specific agent for a trip.
            Data Structure: AgentResult JSON.
            """
            return f"trip:{trip_id}:{agent}_output"

        @staticmethod
        def events_channel(trip_id: str) -> str:
            """Redis Pub/Sub channel for trip-level events (e.g., agent completion)."""
            return f"trip:{trip_id}:events"

    class Driver:
        """Domain: Driver profiles and performance caching."""
        
        PROFILE_TTL: Final[int] = 86400  # 24 hours - driver snapshot cache
        
        @staticmethod
        def profile(driver_id: str) -> str:
            """
            Driver history snapshot - loaded once per job.
            Data Structure: DriverProfile JSON.
            """
            return f"driver:{driver_id}:profile"

    class Telemetry:
        """Domain: Real-time IoT data and buffer management."""
        
        @staticmethod
        def buffer(device_id: str) -> str:
            """
            Raw telemetry aggregation buffer - Kafka stand-in.
            Data Structure: Redis List of TelemetryPackets.
            """
            return f"telemetry:{device_id}:buffer"