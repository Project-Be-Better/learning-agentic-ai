"""
Scoring Agent — Concrete Implementation

Extends Agent ABC with:
- Tools to read trip context, smoothness logs, harsh events from Redis
- System prompt that orchestrates the scoring workflow
- Injected Redis client and Postgres repo (for later stages)

First step: Prove the agent can call tools and reason about scoring.
Later steps: Wire in domain functions and DB writes.
"""

from typing import Any

from agents.base import Agent
from agents.scoring.tools import SCORING_TOOLS


class ScoringAgent(Agent):
    """
    Concrete agent: Scores trips based on smoothness and driving behaviour.

    Inherits from Agent ABC:
    - __init__: Takes llm, sets agent_name, tools, system_prompt
    - invoke: Runs the LLM with tools (inherited)
    - __repr__/__str__: String representations (inherited)

    What this agent does:
    1. Reads trip context from Redis (driver_id, historical_avg, peer_avg)
    2. Reads smoothness logs (16 windows of jerk, speed, RPM, idle data)
    3. Reads harsh events (brakes, accelerations, corners)
    4. Extracts features (smoothness metrics)
    5. Computes behaviour score (0-100)
    6. Evaluates coaching flags (needs training?)
    7. Returns JSON with scoring result

    This is a stateless agent — each invoke is independent.
    Scoring result is returned via agent state, not written to DB yet.
    (DB writes come in a later stage via ScoringRepo)
    """

    def __init__(self, llm: Any, redis_client: Any = None, repo: Any = None):
        """
        Initialize the Scoring Agent.

        Args:
            llm: LangChain chat model (ChatOpenAI or ChatAnthropic)
            redis_client: Redis client for reading trip context, logs, events
                         (optional — used by tools)
            repo: ScoringRepo instance for DB operations
                 (optional — used in later stages)

        Note: redis_client and repo are stored as instance variables for tools to access.
              They're NOT stored in the LangGraph state (not JSON-serializable).
        """
        # Store injected dependencies (not in state)
        self.redis_client = redis_client
        self.repo = repo

        # System prompt — orchestrates the workflow
        system_prompt = """
You are the TraceData Scoring Agent. Your job is to evaluate a truck driver's
trip quality based on driving smoothness and behaviour.

WORKFLOW:
1. Get the trip context (driver ID, historical average score, peer group average)
2. Get smoothness logs (16 windows of jerk, speed, RPM, idle metrics)
3. Get harsh events (braking, acceleration, cornering incidents)
4. Extract smoothness features from the logs
5. Compute behaviour score (0-100) using the features
6. Evaluate coaching needs based on harsh event rates
7. Return a complete scoring result with:
   - behaviour_score: numeric score 0-100
   - score_label: Excellent / Good / Average / Below Average / Poor
   - score_breakdown: component scores for jerk, speed, lateral, engine
   - coaching_required: true if driver needs coaching

USE THESE TOOLS:
- get_trip_context(trip_id): Fetch driver context, trip distance, historical averages
- get_smoothness_logs(trip_id): Fetch 6-16 windows of smoothness data
- get_harsh_events(trip_id): Fetch harsh braking, acceleration, corner events
- compute_behaviour_score(...): Calculate final score from smoothness features

DECISION RULES:
- Score is based on SMOOTHNESS only (jerk, speed consistency, cornering smoothness)
- Harsh events NEVER reduce the score — they only trigger coaching flags
- Peer group average provides context (is this driver above/below peers?)
- Historical average shows trend (is this trip better/worse than usual?)

Remember:
- A driver who brakes hard to avoid a pedestrian should NOT have their score reduced
- A driver with consistent, smooth motion gets a higher score
- Score = smoothness question: "How smoothly did you drive?"
- Coaching = behaviour question: "Do you need training in this area?"

Always use the tools first. Get the data. Then reason about it.
"""

        # Initialize parent Agent ABC
        super().__init__(
            llm=llm,
            agent_name="ScoringAgent",
            tools=SCORING_TOOLS,
            system_prompt=system_prompt,
        )

    def invoke_with_trip(self, trip_id: str) -> dict:
        """
        Convenience method: Score a specific trip.

        Args:
            trip_id: Trip to score

        Returns:
            LangGraph result dict with messages and final scoring JSON
        """
        input_data = {
            "messages": [
                {
                    "role": "user",
                    "content": f"""
Score this trip: {trip_id}

Steps:
1. Get trip context
2. Get smoothness logs and compute features
3. Get harsh events
4. Compute behaviour score using compute_behaviour_score tool
5. Evaluate coaching needs based on event rates
6. Return JSON with score, label, breakdown, coaching_required

Return only valid JSON with these fields:
{{
  "trip_id": "{trip_id}",
  "behaviour_score": <0-100>,
  "score_label": "Excellent|Good|Average|Below Average|Poor",
  "score_breakdown": {{
    "jerk_component": <0-40>,
    "speed_component": <0-25>,
    "lateral_component": <0-20>,
    "engine_component": <0-15>
  }},
  "coaching_required": <true|false>,
  "coaching_reasons": ["reason1", "reason2"]
}}
""",
                }
            ]
        }

        return self.invoke(input_data)
