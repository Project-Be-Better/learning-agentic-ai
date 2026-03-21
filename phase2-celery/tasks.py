import time
from celery import Celery
from typing import Final
from enum import IntEnum, Enum
from pydantic import BaseModel

# CELERY APP

app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)

app.conf.broker_transport_options = {
    "priority_steps": list(range(10)),
    "queue_order_strategy": "priority",
}


# ENUMS
# IntEnum means each value IS an int — priority=Priority.CRITICAL
# works directly with Celery's priority parameter
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


# RESULT MODELS


class SafetyResult(BaseModel):
    """
    Output contract for the Safety Agent
    """

    trip_id: str
    agent: str
    score: float
    flags: list[str]


class ScoringResult(BaseModel):
    """
    Output contract for the Scoring Agent
    """

    trip_id: str
    agent: str
    score: float


class SentimentResult(BaseModel):
    """
    Output contract for the Sentiment Agent
    """

    trip_id: str
    agent: str
    mood: str


# TASKS


@app.task(queue=Queue.SAFETY, name="tracedata.safety.analyse_trip")
def safety_task(trip_id: str) -> dict:
    """
    Safety Agent — analyses driving events for a given trip.
    Returns a SafetyResult serialised as dict (Celery requires dict).
    """
    print(f"[Safety]  picking up {trip_id}...")
    time.sleep(2)

    result: SafetyResult = SafetyResult(
        trip_id=trip_id,
        agent="safety",
        score=0.82,
        flags=["harsh_braking"],
    )
    print(f"[Safety] done {trip_id}")
    return result.model_dump()


@app.task(queue=Queue.SCORING, name="tracedata.scoring.score_trip")
def scoring_task(trip_id: str) -> dict:
    """
    Scoring Agent — computes overall driver score
    """
    print(f"[Scoring]  picking up {trip_id}...")
    time.sleep(4)

    result: ScoringResult = ScoringResult(
        trip_id=trip_id,
        agent="scoring",
        score=0.76,
    )

    print(f"[Scoring]  done {trip_id}")
    return result.model_dump()


@app.task(queue=Queue.SENTIMENT, name="tracedata.sentiment.analyse_sentiment")
def sentiment_task(trip_id: str) -> dict:
    """
    Sentiment Agent — analyses driver feedback
    """
    print(f"[Sentiment] picking up {trip_id}...")
    time.sleep(6)

    result: SentimentResult = SentimentResult(
        trip_id=trip_id,
        agent="sentiment",
        mood="neutral",
    )

    print(f"[Sentiment] done {trip_id}")
    return result.model_dump()
