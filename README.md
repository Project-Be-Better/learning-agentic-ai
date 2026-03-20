# learning-agentic-ai

A walking skeleton for a **multi-agent agentic AI** application built with:

| Component | Technology |
|-----------|-----------|
| Package manager | [uv](https://docs.astral.sh/uv/) |
| Task queue / agents | [Celery](https://docs.celeryq.dev/) + Redis |
| Message broker & result backend | Redis |
| Relational store | PostgreSQL |
| ORM / migrations | SQLAlchemy + Alembic |
| UI for Redis | [Redis Commander](https://github.com/joeferner/redis-commander) |

## Project layout

```
.
├── src/
│   └── agentic_ai/
│       ├── agents/
│       │   ├── base.py           # BaseAgent ABC
│       │   └── example_agent.py  # Starter agent (extend this)
│       ├── db/
│       │   └── session.py        # SQLAlchemy engine & session
│       ├── tasks/
│       │   └── agent_tasks.py    # Celery tasks that wrap agents
│       ├── celery_app.py         # Celery application factory
│       ├── config.py             # Settings from env vars
│       └── main.py               # CLI entry point
├── docker-compose.yml            # postgres + redis + celery worker
├── Dockerfile                    # Worker image
├── .env.example                  # Copy to .env and fill in values
└── pyproject.toml                # uv / PEP 517 project metadata
```

## Quick start

### 1. Install dependencies

```bash
uv sync
```

### 2. Configure environment

```bash
cp .env.example .env
# edit .env if needed
```

### 3. Start infrastructure

```bash
docker compose up -d postgres redis redis-commander
```

### 4. Monitor Redis (Optional)

You can access the Redis Commander Web UI at [http://localhost:8081](http://localhost:8081) to browse keys and monitor Celery queues.

### 4. Start a Celery worker (locally)

```bash
uv run celery -A agentic_ai.celery_app worker --loglevel=info
```

Or bring up the full stack (including the worker container):

```bash
docker compose up --build
```

### 5. Dispatch a task

```bash
uv run python main.py
```

## Adding a new agent

1. Create `src/agentic_ai/agents/my_agent.py` and subclass `BaseAgent`.
2. Add a corresponding Celery task in `src/agentic_ai/tasks/agent_tasks.py`.
3. Dispatch the task from wherever you need it.
