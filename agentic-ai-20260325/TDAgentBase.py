from abc import ABC, abstractmethod
from typing import Dict, Any, TypedDict
from datetime import datetime, timezone
from enum import StrEnum
import hmac
import hashlib
import time
from intent_gate import SecurityError, TDAgentState, verify_intent_capsule


class TDAgentEnum(StrEnum):
    SCORING_AGENT = "scoring_agent"
    SAFETY_AGENT = "safety_agent"


class TDAgentBase(ABC):
    """
    Base Class
    """

    def __init__(self, agent_id: TDAgentEnum, secret_key: str = "dev_secret") -> None:
        """
        Constructor
        """
        self.agent_id = agent_id.value
        self.secret_key = secret_key

    @abstractmethod
    def _execute_logic(self, trip_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        The only method that should be overridden
        1. TAKE input
        2. PERFORM work
        3. RETURN output
        """
        return trip_context

    def _verify_intent_capsule(self, capsule: Dict[str, Any], requested_action: str):
        # Verify Signature
        capsule_data = {
            "trip_id": capsule["trip_id"],
            "expires_at": capsule["expires_at"],
            "allowed_actions": capsule["allowed_actions"],
        }

        expected_signature = hmac.new(
            self.secret_key.encode(), str(capsule_data).encode(), hashlib.sha256
        ).hexdigest()

        if capsule.get("signature") != expected_signature:
            raise SecurityError("Capsule signature mismatch. Tampering detected.")

        # Check 2: Expiration
        if capsule["expires_at"] < time.time():
            raise SecurityError(f"Capsule expired at {capsule['expires_at']}")

        # Check 3: Action bounds
        if requested_action not in capsule.get("allowed_actions", []):
            raise SecurityError(f"Action '{requested_action}' not allowed by capsule")

        return True

    @verify_intent_capsule
    def run(self, state: TDAgentState) -> Dict[str, Any]:
        """
        Public API
        4. CALLS the business logic
        5.
        6. Returns the output as JSON
        Run the agent with Intent Capsule in state.

        State structure:
          - trip_id: "TRIP-001"
          - trip_context: {trip_pings, safety_output, ...}
          - intent_capsule: {capsule_data, signature, ...}
        """
        # Step 1: logic (read trip_context only)
        trip_id = state["trip_id"]
        trip_context = state["trip_context"]

        agent_output = self._execute_logic(trip_context)

        # Step 2: Wrap with metadata
        result = {
            "agent": self.agent_id,
            "trip_id": trip_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status": "SUCCESS",
            "output": agent_output,
        }
        return result
