import time
from celery import Celery

# ── CELERY APP ──────────────────────────────────────────
# First argument: name of this module
# broker: where tasks are queued (Redis)
# backend: where results are stored (Redis)

app = Celery(
    "tasks", broker="redis://localhost:6379/0", backend="redis://localhost:6379/0"
)

# ← Add this for Windows
# app.conf.worker_pool = "solo"


# ── TASK DEFINITION ─────────────────────────────────────
# @app.task turns a regular function into a Celery task
# Any code here runs INSIDE the worker process, not the caller


@app.task
def analyse_trip(trip_id: str, agent: str) -> dict:
    """
    Simulates an agent analysing a trip.
    This runs inside the worker — not in the calling process.
    """
    print(f"[{agent}] picking up trip {trip_id}...")

    # simulate work
    time.sleep(2)

    result: dict = {"trip_id": trip_id, "agent": agent, "status": "done", "score": 0.82}

    print(f"[{agent}] finished trip {trip_id}")
    return result
