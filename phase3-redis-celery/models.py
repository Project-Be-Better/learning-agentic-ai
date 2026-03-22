from enum import IntEnum, Enum
from pydantic import BaseModel


# ENUMS


class Priority(IntEnum):
    """
    Task priority levels for Celery queues.
    Lower number = higher priority. CRITICAL jumps the queue.
    """

    CRITICAL = 0
    HIGH = 3
    MEDIUM = 6
    LOW = 9


class Queue(str, Enum):
    """
    Queue name constants.
    Each agent owns exactly one queue.
    """

    SAFETY = "safety_queue"
    SCORING = "scoring_queue"
    SENTIMENT = "sentiment_queue"


class AgentName(str, Enum):
    """
    Agent name constants.
    Used as identifiers in Redis keys and event payloads.
    """

    SAFETY = "safety"
    SCORING = "scoring"
    SENTIMENT = "sentiment"


# TASK PAYLOAD


class TripTask(BaseModel):
    """
    The payload the Orchestrator sends to every agent.
    Every agent receives this — it tells them what to process.
    """

    trip_id: str
    driver_id: str
    priority: Priority


# AGENT RESULTS


class SafetyResult(BaseModel):
    """Output contract for the Safety Agent."""

    trip_id: str
    agent: AgentName
    score: float
    flags: list[str]


class ScoringResult(BaseModel):
    """Output contract for the Scoring Agent."""

    trip_id: str
    agent: AgentName
    score: float


class SentimentResult(BaseModel):
    """Output contract for the Sentiment Agent."""

    trip_id: str
    agent: AgentName
    mood: str


# COMPLETION EVENT


class CompletionEvent(BaseModel):
    """
    Published to Redis Pub/Sub when an agent finishes.
    Orchestrator listens for these to know when to advance.
    """

    trip_id: str
    agent: AgentName
    status: str
    final: bool = False
