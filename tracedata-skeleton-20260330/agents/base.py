from abc import ABC
from typing import Any

from langgraph.prebuilt import create_react_agent

from agents.logger import get_agent_logger


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
        self.logger = get_agent_logger(agent_name)
        self.logger.info(
            "initialized agent | tools=%s | llm=%s",
            [t.name for t in self.tools],
            type(self.llm).__name__,
        )

    def _create_agent(self):
        self.logger.info("creating langgraph agent")
        return create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=self.system_prompt,
        )

    def invoke(self, input_data: dict) -> dict:
        self.logger.info(
            "invoke start | keys=%s",
            list(input_data.keys()),
        )
        if self._agent is None:
            self._agent = self._create_agent()
        result = self._agent.invoke(input_data)
        self.logger.info("invoke complete")
        return result

    def __repr__(self) -> str:
        return f"{self.agent_name}(tools={len(self.tools)})"

    def __str__(self) -> str:
        tools_str = ", ".join([t.name for t in self.tools])
        return f"{self.agent_name}\n  Tools: {tools_str}\n  LLM: {self.llm}"
