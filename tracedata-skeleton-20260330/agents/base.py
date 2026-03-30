from abc import ABC
from typing import Any

from langgraph.precompiled import create_react_agent


class Agent(ABC):
    """Base class for all TraceData agents."""

    def __init__(
        self,
        llm: Any,
        agent_name: str,
        tools: list,
        system_prompt: str,
    ):
        self.llm = llm
        self.agent_name = agent_name
        self.tools = tools
        self.system_prompt = system_prompt
        self._agent = None

    def _create_agent(self):
        return create_react_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=self.system_prompt,
        )

    def invoke(self, input_data: dict) -> dict:
        if self._agent is None:
            self._agent = self._create_agent()
        return self._agent.invoke(input_data)

    def __repr__(self) -> str:
        return f"{self.agent_name}(tools={len(self.tools)})"

    def __str__(self) -> str:
        tools_str = ", ".join([t.name for t in self.tools])
        return f"{self.agent_name}\n  Tools: {tools_str}\n  LLM: {self.llm}"
