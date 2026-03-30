from agents.base import Agent


class ExampleWeatherTrafficAgent(Agent):
    """Example concrete agent: Weather and traffic evaluation."""

    def __init__(self, llm):
        system_prompt = """
        You are the Weather and Traffic Agent.

        Your job:
        1. Check weather for the given location
        2. Check traffic for the given location
        3. Assess: Are conditions suitable for driving?

        Provide assessment in this format:
        - Weather: [summary]
        - Traffic: [summary]
        - Driving Conditions: [SAFE / CAUTION / UNSAFE]
        - Reason: [why]
        """

        super().__init__(
            llm=llm,
            agent_name="WeatherTrafficAgent",
            tools=[],
            system_prompt=system_prompt,
        )


class ExampleScoringAgent(Agent):
    """Example concrete agent: Trip scoring."""

    def __init__(self, llm):
        system_prompt = """
        You are the Scoring Agent in TraceData.

        Your job:
        1. Get safety context from the Safety Agent
        2. Score the driver (0-100)
        3. Score the trip (0-100)
        4. Decide: Does this driver need coaching support?

        Return your observation with:
        - trip_score
        - driver_score
        - support_flag (True/False)
        - reasoning
        """

        super().__init__(
            llm=llm,
            agent_name="ScoringAgent",
            tools=[],
            system_prompt=system_prompt,
        )


class ExampleOrchestratorAgent(Agent):
    """Example concrete agent: Orchestrator."""

    def __init__(self, llm):
        system_prompt = """
        You are the TraceData Orchestrator Agent.

        Your job:
        1. Delegate to Safety Agent for safety assessment
        2. Delegate to Scoring Agent for trip/driver scores
        3. Delegate to Coaching Agent for recommendations
        4. Synthesize final recommendation

        Use the observations from each agent to make the final decision.
        """

        super().__init__(
            llm=llm,
            agent_name="OrchestratorAgent",
            tools=[],
            system_prompt=system_prompt,
        )
