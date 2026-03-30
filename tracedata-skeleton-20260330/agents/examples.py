from tools.conditions import get_traffic, get_weather

from agents.base import Agent
from agents.prompts import (
    ORCHESTRATOR_SYSTEM_PROMPT,
    SCORING_SYSTEM_PROMPT,
    WEATHER_TRAFFIC_SYSTEM_PROMPT,
)


class ExampleWeatherTrafficAgent(Agent):
    """Example concrete agent: Weather and traffic evaluation."""

    def __init__(self, llm):
        super().__init__(
            llm=llm,
            agent_name="WeatherTrafficAgent",
            tools=[get_weather, get_traffic],
            system_prompt=WEATHER_TRAFFIC_SYSTEM_PROMPT,
        )


class ExampleScoringAgent(Agent):
    """Example concrete agent: Trip scoring."""

    def __init__(self, llm):
        super().__init__(
            llm=llm,
            agent_name="ScoringAgent",
            tools=[],
            system_prompt=SCORING_SYSTEM_PROMPT,
        )


class ExampleOrchestratorAgent(Agent):
    """Example concrete agent: Orchestrator."""

    def __init__(self, llm):
        super().__init__(
            llm=llm,
            agent_name="OrchestratorAgent",
            tools=[],
            system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        )
