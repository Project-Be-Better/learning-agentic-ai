"""Application entry point."""

from agentic_ai.tasks.agent_tasks import run_example_agent


def main() -> None:
    print("Dispatching ExampleAgent task via Celery …")
    result = run_example_agent.delay("hello world")
    print(f"Task id: {result.id}")


if __name__ == "__main__":
    main()
