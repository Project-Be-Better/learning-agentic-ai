"""Celery application and configuration."""

from celery import Celery

from agentic_ai.config import settings

app = Celery(
    "agentic_ai",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["agentic_ai.tasks.agent_tasks"],
)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
