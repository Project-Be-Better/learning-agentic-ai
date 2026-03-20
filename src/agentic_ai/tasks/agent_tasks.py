"""Celery tasks that dispatch work to agents."""

from agentic_ai.celery_app import app


@app.task(name="run_example_agent")
def run_example_agent(input_data: str) -> dict:
    """Run the ExampleAgent inside a Celery worker."""
    from agentic_ai.agents.example_agent import ExampleAgent

    agent = ExampleAgent()
    return agent.run(input_data)
