"""
Orchestrator Agent — Trip Routing and Decision-Making

Extends Agent ABC with trip routing logic.
Makes decisions about which agents should run for a given trip.

Architecture:
  Inheritance: Agent ABC (tool calling, LLM reasoning)
  Tools: 4 orchestration tools (context, heuristics, rule engine)
  System Prompt: Decision logic for agent routing

This agent:
1. Analyzes trip context (priority, events, history)
2. Decides which agents should run (Safety? Scoring? Coaching?)
3. Returns routing decision as JSON
4. Does NOT dispatch tasks itself (that's Celery's job later)
"""

from typing import Any

from agents.base import Agent
from agents.orchestrator.tools import ORCHESTRATOR_TOOLS


class OrchestratorAgent(Agent):
    """
    Orchestrator Agent: Routes trips through the multi-agent system.

    Pattern: Identical to ScoringAgent
    - Inherits from Agent ABC
    - Has tools + system prompt
    - Invokes via LLM reasoning
    - Returns decision as JSON

    What this agent does:
    1. Loads trip context (priority, driver history, flagged events)
    2. Evaluates rules to decide agent sequence
    3. For CRITICAL/HIGH: dispatch Safety Agent first
    4. Always for end_of_trip: dispatch Scoring Agent
    5. After scoring: evaluate 3 coaching rules
    6. If coaching needed: mark for Driver Support Agent dispatch

    This is a stateless, decision-making agent.
    It returns routing decisions; Celery handles actual task dispatch.
    """

    def __init__(self, llm: Any):
        """
        Initialize Orchestrator Agent.

        Args:
            llm: LangChain chat model (ChatOpenAI, ChatAnthropic, etc.)

        Note: Orchestrator is simple — just LLM + tools, no complex modules.
        """

        system_prompt = """
You are the TraceData OrchestratorAgent. Your job is to make routing decisions 
for trips flowing through the multi-agent system.

ARCHITECTURE:
- EventMatrix is the SINGLE SOURCE OF TRUTH for event behavior
- You validate decisions (as the "adult in the room" for edge cases)
- You use LLM reasoning to handle unusual situations

YOUR WORKFLOW:
═════════════════════════════════════════════════════════════════════════════

1. LOOKUP EVENT IN EVENTMATRIX
   
   Use tool: get_event_config(trigger_event_type)
   
   This returns:
   - event_type: The event name
   - category: Event category (critical, harsh_events, trip_lifecycle, etc.)
   - priority: 0=CRITICAL, 3=HIGH, 6=MEDIUM, 9=LOW
   - ml_weight: Machine learning weighting factor
   - action: What should happen (source of truth!)
   - agents_from_action: Suggested agents (helper for you)

2. INTERPRET THE ACTION FIELD (This is the key!)
   
   The 'action' field tells you which agents should run:
   
   - "Emergency Alert & 911" → dispatch ["safety"]
   - "Emergency Alert" → dispatch ["safety"]
   - "Fleet Alert" → dispatch ["safety"]
   - "Coaching" → dispatch ["scoring", "driver_support"]
   - "Regulatory" → dispatch ["scoring"]
   - "Scoring" → dispatch ["scoring"]
   - "Sentiment" → dispatch ["sentiment"]
   - "Support" → dispatch ["driver_support"]
   - "HITL" → dispatch ["human_in_the_loop"]
   - "Analytics" → dispatch []
   - "Logging" → dispatch []
   - "Reward Bonus" → dispatch []
   - "Reject & Log" → dispatch []

3. VALIDATE & APPLY CONTEXT (Adult in the room)
   
   The EventMatrix action is your default. But you can apply judgment:
   
   ✓ ALWAYS follow EventMatrix for standard events
   ✓ IF unusual situation: apply reasoning to context
   ✓ IF trip context suggests different priority: note it
   ✓ IF historical behavior suggests coaching: consider it
   
   Example (Validation):
   - Event says "Coaching" → agents ["scoring", "driver_support"]
   - BUT trip context shows this driver is in safe mode
   - THEN: Keep scoring, maybe defer coaching
   - EXPLAIN your reasoning in the decision

4. EVALUATE COACHING RULES (After Scoring)
   
   Coaching is often deferred to AFTER the Scoring Agent completes.
   But you can use the tool now:
   
   Use tool: evaluate_coaching_rules(behaviour_score, historical_avg, 
                                      flagged_events_count)
   
   This returns:
   - coaching_needed: true|false (from 3 rules)
   - triggered_rules: which rules triggered
   - priority_escalation: if true, escalate LOW→MEDIUM
   - new_priority: escalated priority

5. RETURN YOUR DECISION (JSON ONLY)
   
   Return ONLY valid JSON, no extra text:
   
   {
     "trip_id": "TRIP-...",
     "trigger_event_type": "harsh_brake",
     "priority": 3,
     "agents_to_dispatch": ["scoring", "driver_support"],
     "action": "Coaching",
     "validation": {
       "followed_eventmatrix": true,
       "edge_cases": [],
       "notes": ""
     },
     "reasoning": "EventMatrix action 'Coaching' maps to ['scoring', 'driver_support'].
                   No edge cases detected. Standard workflow."
   }

KEY PRINCIPLES:
═════════════════════════════════════════════════════════════════════════════

✓ EventMatrix is SINGLE SOURCE OF TRUTH
  - Don't guess, always look it up
  - If event not in matrix, ask to add it

✓ Action field drives agent selection
  - Map action → agents using the mapping above
  - The mapping is deterministic and consistent

✓ You are the "adult in the room"
  - Apply reasoning for edge cases
  - Document your deviations from EventMatrix
  - But default to EventMatrix

✓ Coaching is often deferred
  - Usually evaluated AFTER Scoring Agent completes
  - Handled by event listener, not orchestrator
  - But you can evaluate it now if needed

✓ Priority escalation
  - If coaching needed: escalate LOW (9) → MEDIUM (6)
  - Document the escalation in your reasoning

WORKFLOW EXAMPLE:
═════════════════════════════════════════════════════════════════════════════

Trip: end_of_trip event

1. Call get_event_config("end_of_trip")
   → Returns: action="Scoring", priority=9

2. Map action "Scoring" → agents ["scoring"]

3. Check trip context (safe operation)
   → No edge cases

4. Return:
   {
     "trip_id": "...",
     "trigger_event_type": "end_of_trip",
     "priority": 9,
     "agents_to_dispatch": ["scoring"],
     "action": "Scoring",
     "reasoning": "Standard end_of_trip. EventMatrix action 'Scoring' 
                   maps to ['scoring'] agent."
   }

Another example:

Trip: harsh_brake event with driver in HIGH priority status

1. Call get_event_config("harsh_brake")
   → Returns: action="Coaching", priority=3

2. Map action "Coaching" → agents ["scoring", "driver_support"]

3. Check trip context
   → This driver has poor history, HIGH priority situation
   → Edge case: should coaching priority be escalated?

4. Evaluate coaching rules (if score available)
   → If coaching triggered: escalate to MEDIUM (6)

5. Return:
   {
     "trip_id": "...",
     "trigger_event_type": "harsh_brake",
     "priority": 3,
     "agents_to_dispatch": ["scoring", "driver_support"],
     "action": "Coaching",
     "validation": {
       "followed_eventmatrix": true,
       "edge_cases": ["HIGH priority driver, poor history"],
       "escalation_considered": true
     },
     "reasoning": "EventMatrix action 'Coaching' maps to agents.
                   Edge case noted: HIGH priority driver with poor history.
                   Coaching escalation warranted."
   }

REMEMBER:
═════════════════════════════════════════════════════════════════════════════

- EventMatrix is the source of truth (look it up, don't guess)
- Action field tells you which agents (use the mapping)
- You are the adult (validate, apply context, document edge cases)
- Return JSON only (no extra explanations)
- Be consistent (same event → same routing, unless justified)

Let's route this trip!
"""

        # Initialize parent Agent ABC
        super().__init__(
            llm=llm,
            agent_name="OrchestratorAgent",
            tools=ORCHESTRATOR_TOOLS,
            system_prompt=system_prompt,
        )

    def invoke_with_trip(
        self,
        trip_id: str,
        priority: int,
        trigger_event_type: str,
    ) -> dict:
        """
        Convenience method: Make routing decision for a single trip.

        This is the main entry point. Call this to get routing decisions.

        Args:
            trip_id: Trip identifier
                    (e.g., "TRIP-T12345-2026-03-07-08:00")

            priority: Event priority (0-9)
                     0 = CRITICAL (collision, rollover, SOS)
                     3 = HIGH (harsh events)
                     6 = MEDIUM (speeding, driver feedback)
                     9 = LOW (end_of_trip, idle, normal)

            trigger_event_type: What triggered this orchestration
                               (e.g., "end_of_trip", "collision", "vehicle_offline")

        Returns:
            LangGraph result dict with messages

            Extract decision from: result["messages"][-1].content
            (This is a JSON string with routing decision)

        Example Usage:
            ```python
            orchestrator = OrchestratorAgent(llm=llm)

            result = orchestrator.invoke_with_trip(
                trip_id="TRIP-T12345-2026-03-07-08:00",
                priority=9,
                trigger_event_type="end_of_trip"
            )

            # Extract decision
            decision_json_str = result["messages"][-1].content
            decision = json.loads(decision_json_str)

            print(f"Agents to dispatch: {decision['agents_to_dispatch']}")
            # Output: Agents to dispatch: ['scoring']
            ```

        Example Decision Output:
            ```json
            {
              "trip_id": "TRIP-T12345-2026-03-07-08:00",
              "trigger_event_type": "end_of_trip",
              "priority": 9,
              "agents_to_dispatch": ["scoring"],
              "safety_agent_needed": false,
              "scoring_agent_needed": true,
              "coaching_decision_deferred": true,
              "reasoning": "LOW priority (9) and non-critical trigger.
                            Safety Agent not needed. Scoring Agent always
                            runs for end_of_trip. Coaching decision deferred
                            until after scoring completes."
            }
            ```
        """

        input_data = {
            "messages": [
                {
                    "role": "user",
                    "content": f"""
Route this trip through the multi-agent system:

TRIP INFORMATION:
- Trip ID: {trip_id}
- Priority: {priority} (0=CRITICAL, 3=HIGH, 6=MEDIUM, 9=LOW)
- Trigger Event: {trigger_event_type}

YOUR DECISION PROCESS:
1. Call get_trip_context(trip_id) to load metadata
2. Call should_dispatch_safety_agent(priority, trigger_event_type)
3. Call should_dispatch_scoring_agent(trigger_event_type)
4. Combine heuristics to decide agent sequence
5. Return JSON with routing decision

Return ONLY valid JSON (no extra text). Use this structure:
{{
  "trip_id": "{trip_id}",
  "trigger_event_type": "{trigger_event_type}",
  "priority": {priority},
  "agents_to_dispatch": [...],           // List of agents: "safety", "scoring"
  "safety_agent_needed": true|false,
  "scoring_agent_needed": true|false,
  "coaching_decision_deferred": true,    // Always true (deferred to next step)
  "reasoning": "..."
}}

Go!
""",
                }
            ]
        }

        return self.invoke(input_data)
