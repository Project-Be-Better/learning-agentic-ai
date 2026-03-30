---
name: create-celery-task
description: Instructions for wrapping agents into Celery tasks.
---

# Create Celery Task Skill

Use this skill when you need to expose a new agent as a background task.

## Core Pattern

Tasks should be defined in `src/agentic_ai/tasks/agent_tasks.py` (or a module-specific tasks file) and use the `app` instance from `celery_app.py`.

```python
from agentic_ai.celery_app import app
from typing import Dict, Any

@app.task(name="run_my_new_agent")
def run_my_new_agent(state_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Background wrapper for MyNewAgent.
    """
    # 1. LAZY IMPORT (CRITICAL)
    # Import inside the task to avoid circular dependencies 
    # and ensures the agent class is only loaded where needed.
    from agentic_ai.agents.my_new_agent import MyNewAgent
    from agentic_ai.models import TDAgentState

    # 2. HYDRATE STATE
    # Convert input dict to TDAgentState Pydantic model
    state = TDAgentState(**state_dict)

    # 3. RUN AGENT
    agent = MyNewAgent()
    result = agent.run(state)

    # 4. RETURN RESULT DICT
    # Return model_dump() so Celery can serialize the JSON result.
    return result.model_dump()
```

## Task Naming

Always provide a explicit `name` in the `@app.task()` decorator.
Pattern: `run_{agent_name}`

## Error Handling

TDAgentBase catches most internal errors and logs them. If a task fails critically, Celery will mark the task as `FAILURE`.

## Best Practices

- **Input**: Pass only primitive types (dict, str, int) as task arguments. Use Pydantic to validate them inside the task.
- **Output**: Return a JSON-serializable dictionary (use `model_dump()`).
- **Imports**: Always use imports inside the task function for agent classes.
