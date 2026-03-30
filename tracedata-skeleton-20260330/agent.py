"""
Agent ABC: Base class for all agents in TraceData

Pattern:
  - Agent ABC: Abstract base class (this file)
  - Concrete agents inherit from Agent
  - Each agent defines: agent_name, tools, system_prompt
  - No boilerplate duplication

Integration:
  - Works with LLM adapter (load_llm() returns LLMConfig)
  - Uses LangGraph's create_react_agent
  - Multi-turn reasoning with tool calling
"""

from abc import ABC
from typing import Any

from langgraph.precompiled import create_react_agent

# =============================================================================
# SECTION 1: AGENT ABC (Base class for all agents)
# =============================================================================


class Agent(ABC):
    """
    Abstract Base Class for all TraceData agents.

    Handles:
    - LLM initialization (from LLM adapter)
    - Tool management
    - LangGraph ReAct agent creation
    - Invocation (multi-turn reasoning with tool calling)

    Concrete agents (ScoringAgent, SafetyAgent, etc.) inherit from this class
    and only define:
    - agent_name: Unique identifier
    - tools: List of tools the agent can call
    - system_prompt: Instructions for agent behavior

    No code duplication. Just configuration.
    """

    def __init__(
        self,
        llm: Any,
        agent_name: str,
        tools: list,
        system_prompt: str,
    ):
        """
        Initialize an agent.

        Args:
            llm: LangChain chat model instance
                 (from LLMAdapter.get_chat_model())
                 Examples:
                   - ChatOpenAI (from langchain_openai)
                   - ChatAnthropic (from langchain_anthropic)

            agent_name: Unique identifier for this agent
                        Examples: "ScoringAgent", "SafetyAgent", "OrchestratorAgent"

            tools: List of LangChain tools the agent can call
                   Each tool is decorated with @tool
                   Example: [get_safety_context, score_driver, score_trip]

            system_prompt: Instructions for the agent's behavior
                           Tells the agent:
                           - What its job is
                           - What tools are available
                           - How to use them
                           - What output format to use
        """
        self.llm = llm
        self.agent_name = agent_name
        self.tools = tools
        self.system_prompt = system_prompt
        self._agent = None  # Lazy-loaded (created on first invoke)

    def _create_agent(self):
        """
        Create the LangGraph ReAct agent.

        This is called once on first invoke (lazy loading).

        LangGraph's create_react_agent:
        - Takes the LLM and tools
        - Creates an agent loop:
          1. LLM thinks about what to do
          2. Decides which tool to call
          3. Executes the tool
          4. Gets observation (result)
          5. Feeds observation back to LLM
          6. Repeats until LLM returns final answer (no more tools)

        Returns:
            A compiled LangGraph agent ready to invoke
        """
        return create_react_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=self.system_prompt,
        )

    def invoke(self, input_data: dict) -> dict:
        """
        Run the agent with the given input.

        The agent will:
        1. Receive input_data with initial user message(s)
        2. Think about what to do
        3. Call tools as needed
        4. Synthesize a final answer
        5. Return the complete state (messages + results)

        Args:
            input_data: Dict with structure:
                        {
                          "messages": [
                            {"role": "user", "content": "..."}
                          ]
                        }

                        The agent will add its own messages to this list
                        as it thinks and acts.

        Returns:
            Dict with structure:
            {
              "messages": [
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."},
                ...
              ]
            }

            The last message is the agent's final response.
        """
        # Lazy-create the agent on first invoke
        if self._agent is None:
            self._agent = self._create_agent()

        # Run the agent
        return self._agent.invoke(input_data)

    def __repr__(self) -> str:
        """String representation of the agent."""
        return f"{self.agent_name}(tools={len(self.tools)})"

    def __str__(self) -> str:
        """Human-readable representation."""
        tools_str = ", ".join([t.name for t in self.tools])
        return f"{self.agent_name}\n  Tools: {tools_str}\n  LLM: {self.llm}"


# =============================================================================
# SECTION 2: EXAMPLE CONCRETE AGENTS
# =============================================================================
# These are examples. You'll create real ones with actual tools.


class ExampleWeatherTrafficAgent(Agent):
    """
    Example concrete agent: Weather & Traffic evaluation.

    This is a minimal example showing how to extend Agent ABC.
    """

    def __init__(self, llm):
        """
        Initialize the Weather/Traffic Agent.

        Inherits all common logic from Agent ABC.
        Only defines: agent_name, tools, system_prompt
        """
        # Import tools (would be defined in separate module)
        # from tools.weather import get_weather, get_traffic

        system_prompt = """
You are the Weather & Traffic Agent.

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
            tools=[],  # Would add actual tools here: [get_weather, get_traffic]
            system_prompt=system_prompt,
        )


class ExampleScoringAgent(Agent):
    """
    Example concrete agent: Trip scoring.

    This is how you'd create the ScoringAgent for TraceData.
    """

    def __init__(self, llm):
        """
        Initialize the Scoring Agent.

        Would call tools like:
        - get_safety_context: Read safety assessment
        - score_driver: XGBoost inference on driver
        - score_trip: XGBoost inference on trip
        """
        # from tools.scoring import get_safety_context, score_driver, score_trip

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
            tools=[],  # Would add: [get_safety_context, score_driver, score_trip]
            system_prompt=system_prompt,
        )


class ExampleOrchestratorAgent(Agent):
    """
    Example concrete agent: Orchestrator.

    Coordinates all other agents.
    """

    def __init__(self, llm):
        """
        Initialize the Orchestrator Agent.

        Would call tools like:
        - invoke_safety_agent
        - invoke_scoring_agent
        - invoke_coaching_agent

        Then synthesizes final recommendation.
        """
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
            tools=[],  # Would add agent-calling tools
            system_prompt=system_prompt,
        )


# =============================================================================
# SECTION 3: USAGE EXAMPLE
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Agent ABC: Base Class for All Agents")
    print("=" * 70 + "\n")

    print("This file provides the Agent ABC base class.")
    print("\nTo create a concrete agent:\n")

    print("""
from llm_adapter import load_llm
from agent_base import Agent
from langchain_core.tools import tool

# Step 1: Define tools
@tool
def my_tool(input: str) -> str:
    \"\"\"My tool description\"\"\"
    return f"Result: {input}"

# Step 2: Create concrete agent (inherits from Agent)
class MyAgent(Agent):
    def __init__(self, llm):
        super().__init__(
            llm=llm,
            agent_name="MyAgent",
            tools=[my_tool],
            system_prompt="You are MyAgent. Use your tools to..."
        )

# Step 3: Use the agent
config = load_llm()
llm = config.adapter.get_chat_model()

agent = MyAgent(llm=llm)
result = agent.invoke({
    "messages": [
        {"role": "user", "content": "Your query here"}
    ]
})

print(result["messages"][-1])  # Final response
""")

    print("\nBenefits of this pattern:")
    print("  ✓ No boilerplate duplication")
    print("  ✓ Easy to add new agents (5 lines of code)")
    print("  ✓ Consistent interface across all agents")
    print("  ✓ All agents use same LLM (from adapter)")
    print("  ✓ Easy to test each agent independently\n")
