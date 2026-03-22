from typing import Final
from models import AgentName


class RedisSchema:
    """
    Centralized Redis Key Schema for Tracedata
    All keys and TTLs defined in one place
    No agent ever hardcodes a key string
    """

    class Trip:
        """
        Domain: Vehicle trips, agent coordination, and results
        """

        CONTEXT_TTL: Final[int] = 7200  # 2 hours — active trip window
        OUTPUT_TTL: Final[int] = 3600  # 1 hour  — agent output cache
        EVENT_TTL: Final[int] = 1800  # 30 mins — completion event log

        @staticmethod
        def context(trip_id: str) -> str:
            """
            Key for the full trip context (Pickup, Destination, Status)
            Data Structure: TripContext JSON

            Full trip context loaded by Orchestrator at job start
            Read by all agents on task pickup
            """
            return f"trip:{trip_id}:context"

        @staticmethod
        def output(trip_id: str, agent: AgentName) -> str:
            """
            Output written by a specific agent for a trip
            Data Structure: AgentResult JSON

            Read by Orchestrator after agent completes
            """
            return f"trip:{trip_id}:{agent.value}_output"

        @staticmethod
        def events_channel(trip_id: str) -> str:
            """
            Redis Pub/Sub channel for trip-level events (e.g., agent completion)

            Agents publish here on completion. Orchestrator subscribes
            """
            return f"trip:{trip_id}:events"

    class Driver:
        """
        Domain: Driver profiles and performance caching
        """

        PROFILE_TTL: Final[int] = 86400  # 24 hours — driver snapshot cache

        @staticmethod
        def profile(driver_id: str) -> str:
            """
            Driver history snapshot - loaded once per job
            Data Structure: DriverProfile JSON

            Read by all agents on task pickup
            Shared across all agents for context
            """
            return f"driver:{driver_id}:profile"

    class Telemetry:
        """
        Domain: Real-time IoT data and buffer management
        """

        @staticmethod
        def buffer(device_id: str) -> str:
            """
            Raw telemetry aggregation buffer - Kafka stand-in
            Data Structure: Redis List of TelemetryPackets
            """
            return f"telemetry:{device_id}:buffer"
