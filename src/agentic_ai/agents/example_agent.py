"""Example agent — replace with your own logic."""

from typing import Any

from agentic_ai.agents.base import BaseAgent


class ExampleAgent(BaseAgent):
    name = "example_agent"

    def run(self, input_data: Any) -> dict:
        # TODO: implement your agent logic here
        return {"agent": self.name, "result": f"processed: {input_data}"}
