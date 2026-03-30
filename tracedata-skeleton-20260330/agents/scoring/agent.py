"""
Scoring Agent — Concrete Implementation with XAI and Fairness

Extends Agent ABC with:
- Tools to read trip context, smoothness logs, harsh events from Redis
- COMPOSITE tool for scoring + explaining + auditing fairness
- Injected XAI engine (SHAPExplainer) and fairness auditor (FairnessAuditor)
- System prompt that orchestrates the complete scoring workflow

Architecture:
  Inheritance: Agent ABC (tool calling, LLM reasoning)
  Composition: SHAPExplainer module, FairnessAuditor module
  Tools: 4 tools including composite score_and_audit_trip

This demonstrates the pattern: Agent ABC handles tool orchestration,
while modules handle specific domain logic (XAI, Fairness).
"""

from typing import Any

from agents.base import Agent
from agents.scoring.fairness import FairnessAuditor
from agents.scoring.tools import SCORING_TOOLS
from agents.scoring.xai import SHAPExplainer


class ScoringAgent(Agent):
    """
    Scoring Agent with XAI and Fairness capabilities.

    Inherits from Agent ABC:
    - __init__: Takes llm, sets agent_name, tools, system_prompt
    - invoke: Runs the LLM with tools (inherited)
    - __repr__/__str__: String representations (inherited)

    Composes:
    - SHAPExplainer: For explaining trip scores
    - FairnessAuditor: For auditing fairness/bias

    What this agent does:
    1. Reads trip context from Redis (driver_id, demographics, historical_avg)
    2. Reads smoothness logs (16 windows of jerk, speed, RPM, idle data)
    3. Reads harsh events (brakes, accelerations, corners)
    4. Computes behaviour score (0-100) with explanation (SHAP)
    5. Audits fairness (demographic bias checks with AIF360)
    6. Returns complete result: score + explanation + audit

    This is a stateless agent — each invoke is independent.
    Results are returned via agent state, not written to DB yet.
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

        Note: Modules (xai_engine, fairness_auditor) are stored as instance variables
              so tools can access them via closure or dependency injection.
              They're NOT stored in the LangGraph state (not JSON-serializable).
        """
        # Store injected dependencies (not in state)
        self.redis_client = redis_client
        self.repo = repo

        # Compose XAI module
        self.xai_engine = (
            SHAPExplainer(
                model=repo.load_xgboost_model() if repo else None,
                background_data=repo.load_background_data() if repo else None,
            )
            if repo
            else None
        )

        # Compose Fairness module
        self.fairness_auditor = FairnessAuditor(
            protected_attributes=["driver_age", "experience_level"],
            privileged_groups={
                "driver_age": [1, 0],  # Numeric: privileged if >= 1
                "experience_level": ["high", "medium"],  # String: privileged values
            },
        )

        # System prompt — orchestrates the workflow
        system_prompt = """
You are the TraceData Scoring Agent. Your job is to evaluate a truck driver's
trip quality based on driving smoothness, behaviour, and fairness.

WORKFLOW:
1. Get the trip context (driver ID, historical average score, demographics)
2. Get smoothness logs (16 windows of jerk, speed, RPM, idle metrics)
3. Get harsh events (braking, acceleration, cornering incidents)
4. Score the trip AND explain with SHAP AND audit fairness (all in one call)
5. Return a complete scoring result with:
   - behaviour_score: numeric score 0-100
   - score_label: Excellent / Good / Average / Below Average / Poor
   - score_breakdown: component scores for jerk, speed, lateral, engine
   - shap_explanation: SHAP values and feature importance
   - fairness_audit: bias checks and demographic parity analysis

USE THESE TOOLS:
- get_trip_context(trip_id): Fetch driver context, demographics, trip metadata
- get_smoothness_logs(trip_id): Fetch 6-16 windows of smoothness data
- get_harsh_events(trip_id): Fetch harsh braking, acceleration, corner events
- score_and_audit_trip(trip_id, features, demographics): 
    MAIN OPERATION: Score + Explain (SHAP) + Audit (Fairness)
    This is the core tool. It returns everything: score, explanation, and audit.

DECISION RULES:
- Score is based on SMOOTHNESS only (jerk, speed consistency, cornering smoothness)
- Harsh events NEVER reduce the score — they only trigger coaching flags
- Peer group average provides context (is this driver above/below peers?)
- Historical average shows trend (is this trip better/worse than usual?)
- Fairness is checked automatically: no demographic bias allowed
- If score seems unusual for this demographic group, flag it for review

EXPLAINABILITY:
- Every score must be explained (SHAP values show which features drove it)
- Every score must be audited (AIF360 checks for demographic bias)
- Decisions are fully traceable and auditable

Remember:
- A driver who brakes hard to avoid a pedestrian should NOT have their score reduced
- A driver with consistent, smooth motion gets a higher score
- Score = smoothness question: "How smoothly did you drive?"
- Fairness = responsibility question: "Is this score fair across demographic groups?"

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
        Convenience method: Score a specific trip with explanation and audit.

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
1. Get trip context (driver info, demographics)
2. Get smoothness logs (extract features for scoring)
3. Get harsh events (check if coaching needed)
4. Score and audit: Call score_and_audit_trip with features and demographics
   - This returns: score, SHAP explanation, and fairness audit
5. Return JSON with all results

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
  "shap_explanation": {{
    "top_features": [...],
    "narrative": "Human-readable explanation"
  }},
  "fairness_audit": {{
    "demographic_parity": "PASS|WARN|FAIL",
    "equalized_odds": "PASS|WARN|FAIL",
    "bias_detected": <true|false>,
    "recommendation": "..."
  }},
  "coaching_required": <true|false>,
  "coaching_reasons": ["reason1", "reason2"]
}}
""",
                }
            ]
        }

        return self.invoke(input_data)
