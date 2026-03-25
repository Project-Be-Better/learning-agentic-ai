from abc import ABC, abstractmethod
from typing import Dict, Any, TypedDict
from datetime import datetime, timezone
from enum import StrEnum
import hmac
import hashlib
import time
import json
import functools


class SecurityError(Exception):
    """
    Raised when Intent Gate rejects a request
    """

    pass


class TDAgentState(TypedDict):
    """
    Trip Info + Signed Permission
    State passed to agent. Pure JSON-serializable data.

    Fields:
        trip_id: Unique trip identifier
        trip_context: Pre-fetched data (pings, safety output, etc)
        intent_capsule: Signed work order (the capsule)
    """

    trip_id: str
    trip_context: Dict[str, Any]  # Pre-fetched data
    intent_capsule: Dict[str, Any]  # Signed permission slip


def create_intent_capsule(
    trip_id: str,
    secret_key: str,
    expires_at: float,
) -> Dict[str, Any]:
    """
    Create an Intent Capsule (signed work order).

    In real system, Orchestrator calls this before dispatching to agent.
    This creates the "sealed & signed" part of the diagram.

    Args:
        trip_id: The trip being processed
        secret_key: Secret used to sign the capsule
        expires_at: Unix timestamp when capsule expires

    Returns:
        Intent Capsule dict:
        {
          "capsule": {
            "correlation_id": "trip-req-001",
            "trip_id": "TRIP-001",
            "subject": "scoring_agent",
            "purpose": "evaluate_trip_lifecycle",
            "constraints": {
              "allowed_actions": ["score_trip"],
              "resource_id": "redis:trip_summary:001",
              "max_compute_time_seconds": 30
            },
            "issued_at": 1711314000,
            "expires_at": 1711314060
          },
          "signature": "dbb40d70...[HMAC-SHA256]...8c"
        }
    """
    capsule_data = {
        "correlation_id": f"trip-req-{trip_id}",
        "trip_id": trip_id,
        "subject": "scoring_agent",
        "purpose": "evaluate_trip_lifecycle",
        "constraints": {
            "allowed_actions": ["score_trip"],
            "resource_id": f"redis:trip_summary:{trip_id}",
            "max_compute_time_seconds": 30,
        },
        "issued_at": int(time.time()),
        "expires_at": int(expires_at),
    }

    # Sign it (HMAC-SHA256)
    signature = hmac.new(
        secret_key.encode(),
        json.dumps(capsule_data, sort_keys=True).encode(),
        hashlib.sha256,
    ).hexdigest()

    return {
        "capsule": capsule_data,
        "signature": signature,
    }


def verify_intent_capsule(func):
    """
    Intent Gate Decorator (middleware).

    This is the {Intent Gate} in the diagram.

    What it does:
    1. Extracts capsule from state
    2. Verifies signature (capsule hasn't been tampered with)
    3. Checks expiration (capsule is still valid)
    4. If valid → allows agent to execute
    5. If invalid → raises SecurityError, blocks execution

    The agent doesn't know this exists. It's automatic protection
    applied to the run() method.

    Diagram flow:
    Intent Capsule → {Intent Gate} → Verifies signature + expiration
                                  ↓
                        Matches Capsule? → Execute Action
                        Drifts/Invalid? → Block Action
    """

    @functools.wraps(func)
    def wrapper(self, state: TDAgentState) -> Dict[str, Any]:
        """
        Internal: Verify capsule before agent runs.

        Args:
            self: The agent instance (has secret_key)
            state: The state dict with intent_capsule

        Returns:
            Result from the original run() method

        Raises:
            SecurityError: If capsule is invalid or expired
        """
        capsule = state["intent_capsule"]

        # INTENT GATE VALIDATION

        # Check 1: Verify signature (detect tampering)
        capsule_data = capsule["capsule"]
        expected_signature = hmac.new(
            self.secret_key.encode(),
            json.dumps(capsule_data, sort_keys=True).encode(),
            hashlib.sha256,
        ).hexdigest()

        if capsule.get("signature") != expected_signature:
            raise SecurityError(
                f"Intent Capsule TAMPERING DETECTED. " f"Signature mismatch."
            )

        # Check 2: Verify expiration (still within time window)
        current_time = time.time()
        expires_at = capsule_data.get("expires_at")

        if current_time > expires_at:
            raise SecurityError(
                f"Intent Capsule EXPIRED. "
                f"Valid until: {expires_at}, Current: {current_time}"
            )

        # GATE PASSED: Agent is allowed to execute
        return func(self, state)

    return wrapper
