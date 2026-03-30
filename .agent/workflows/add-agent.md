---
description: How to add a new Agent and expose it via Celery
---

# Add Agent Workflow

Follow these steps to implement a new agent and its corresponding background task.

1.  **Create the Agent Implementation**
    - Create a new file `src/agentic_ai/agents/[agent_name].py`.
    - Use the `implement-agent` skill to define the class.
    - Ensure it inherits from `TDAgentBase` and implements `_execute_logic`.

2.  **Add the Celery Task**
    - Open `src/agentic_ai/tasks/agent_tasks.py`.
    - Use the `create-celery-task` skill to define a new `@app.task`.
    - Ensure you use a lazy import for the new agent class.

3.  **Update Config/Enums (Optional)**
    - If needed, add the new agent to `TDAgentEnum` in `agentic_ai/agents/base.py` or equivalent.
    - Update any relevant configuration in `src/agentic_ai/config.py`.

4.  **Verify the Implementation**
    - Create a unit test `tests/test_[agent_name].py`.
    - Run `pytest tests/test_[agent_name].py` to verify the agent's logic.
    - (Optional) Run a local worker and dispatch the task manually to verify Celery integration.
