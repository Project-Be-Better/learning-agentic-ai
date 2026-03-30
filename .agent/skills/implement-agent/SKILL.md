---
name: implement-agent
description: Instructions for implementing a new Agent using the TDAgentBase framework.
---

# Implement Agent Skill

Use this skill when you need to create a new agent in the `src/agentic_ai/agents/` directory.

## Core Pattern

All agents must inherit from `TDAgentBase` (or `BaseAgent` if refined later) and implement the `_execute_logic` method.

```python
from typing import Dict, Any
from agentic_ai.agents.base import TDAgentBase
from agentic_ai.models import AgentOutput, TDAgentState
from agentic_ai.intent_gate import verify_intent_capsule

class MyNewAgent(TDAgentBase):
    def __init__(self, agent_id="my_new_agent", secret_key="dev_secret"):
        super().__init__(agent_id, secret_key)

    @verify_intent_capsule
    def run(self, state: TDAgentState) -> AgentResult:
        # Standard implementation in TDAgentBase handles logging and validation
        return super().run(state)

    def _execute_logic(self, trip_context: Dict[str, Any]) -> AgentOutput:
        """
        Pure business logic goes here.
        - Input: trip_context (pre-fetched data)
        - Output: AgentOutput (structured result)
        """
        # Logic...
        return AgentOutput(
            trip_score=85,
            pings_count=10,
            harsh_events_count=0,
            action="score_trip"
        )
```

## Validation & Security

1. **State Validation**: Always use `TDAgentState` as the input type for `run()`. It ensures `trip_id`, `trip_context`, and `intent_capsule` are present.
2. **Intent Capsule**: Apply the `@verify_intent_capsule` decorator to the `run()` method. This checks the signature and expiration of the work order.

## Context Handling

Access data through the `trip_context` dictionary. The orchestrator is responsible for hydrating this context from Redis before calling the agent.

## Observability

The `TDAgentBase` class provides integrated structured logging.
- Use `self.logger.info()` or `self.logger.error()`.
- The `run()` method automatically wraps execution in a `LogContext` with `correlation_id` and `trip_id`.

## Testing

When testing agents, use the `valid_capsule` fixture and mock the `TDAgentState`.

```python
def test_agent_logic(my_agent, valid_capsule):
    state = TDAgentState(
        trip_id="TRIP-001",
        trip_context={"key": "value"},
        intent_capsule=valid_capsule
    )
    result = my_agent.run(state)
    assert result.status == "success"
```
