"""Application settings loaded from environment variables."""

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://agentic:agentic@localhost:5432/agentic_ai",
    )


settings = Settings()
