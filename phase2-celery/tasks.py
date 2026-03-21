import time
from celery import Celery

# ── CELERY APP ──────────────────────────────────────────
# First argument: name of this module
# broker: where tasks are queued (Redis)
# backend: where results are stored (Redis)

app = Celery(
    "tasks", broker="redis://localhost:6379/0", backend="redis://localhost:6379/0"
)


# ── QUEUE NAMES ─────────────────────────────────────────
# defined once here so dispatcher and workers always agree
SAFETY_QUEUE = "safety_queue"
SCORING_QUEUE = "scoring_queue"
SENTIMENT_QUEUE = "sentiment_queue"

# ← Add this for Windows
# app.conf.worker_pool = "solo"


# ── TASKS ───────────────────────────────────────────────
# queue= tells Celery which queue this task belongs to
# workers will only pick up tasks from their assigned queue
# ── TASK DEFINITION ─────────────────────────────────────
# @app.task turns a regular function into a Celery task
# Any code here runs INSIDE the worker process, not the caller


@app.task(queue=SAFETY_QUEUE)
def safety_task(trip_id: str) -> dict:
    """
    Safety Agent — analyses driving events
    """
    print(f"[Safety]  picking up {trip_id}...")
    time.sleep(2)
    result: dict = {
        "trip_id": trip_id,
        "agent": "safety",
        "score": 0.82,
        "flags": ["harsh_braking"],
    }
    print(f"[Safety] done {trip_id}")
    return result


@app.task(queue=SCORING_QUEUE)
def scoring_task(trip_id: str) -> dict:
    """
    Scoring Agent — computes overall driver score
    """
    print(f"[Scoring]  picking up {trip_id}...")

    time.sleep(4)
    result: dict = {
        "trip_id": trip_id,
        "agent": "scoring",
        "score": 0.76,
    }

    print(f"[Scoring]  done {trip_id}")
    return result


@app.task(queue=SENTIMENT_QUEUE)
def sentiment_task(trip_id: str) -> dict:
    """
    Sentiment Agent — analyses driver feedback
    """
    print(f"[Sentiment] picking up {trip_id}...")
    time.sleep(6)
    result: dict = {
        "trip_id": trip_id,
        "agent": "sentiment",
        "mood": "neutral",
    }
    print(f"[Sentiment] done {trip_id}")
    return result
