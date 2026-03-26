from typing import Dict, Any, TypedDict, Optional
import hmac
import hashlib
import time
import json
import functools
import logging
import uuid

from exceptions import (
    SecurityError,
    TamperingError,
    ExpirationError,
    ConstraintViolationError,
    MissingFieldError,
)

logger = logging.getLogger(__name__)


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
    subject: str = "scoring_agent",
    purpose: str = "evaluate_trip_lifecycle",
    allowed_actions: Optional[list] = None,
    constraints: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create an Intent Capsule (signed work order).

    Flexible for any agent.

    Args:
        trip_id: Trip being processed
        secret_key: Secret used to sign
        expires_at: Unix timestamp when expires
        subject: Agent name (default: "scoring_agent")
        purpose: What this capsule is for (default: "evaluate_trip_lifecycle")
        allowed_actions: List of allowed actions (default: ["score_trip"])
        constraints: Custom constraints dict (overrides auto-generated)

    Returns:
        Signed Intent Capsule dict
    """
    if allowed_actions is None:
        allowed_actions = ["score_trip"]

    if constraints is None:
        constraints = {
            "allowed_actions": allowed_actions,
            "resource_id": f"redis:trip_summary:{trip_id}",
            "max_compute_time_seconds": 30,
        }

    capsule_data = {
        "correlation_id": f"trip-req-{trip_id}",
        "trip_id": trip_id,
        "subject": subject,
        "purpose": purpose,
        "constraints": constraints,
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
            TamperingError: If capsule signature verification fails
            ExpirationError: If capsule has expired
            ConstraintViolationError: If capsule constraints are violated
        """
        security_event_id = str(uuid.uuid4())

        try:
            capsule = state["intent_capsule"]
        except KeyError:
            logger.error(
                json.dumps(
                    {
                        "action": "intent_gate_validation",
                        "status": "failed",
                        "reason": "missing_intent_capsule",
                        "security_event_id": security_event_id,
                        "timestamp": time.time(),
                    }
                )
            )
            raise MissingFieldError("'intent_capsule' is required in state")

        # INTENT GATE VALIDATION

        # Check 1: Verify signature (detect tampering)
        capsule_data = capsule.get("capsule")
        if capsule_data is None:
            logger.error(
                json.dumps(
                    {
                        "action": "intent_gate_validation",
                        "status": "failed",
                        "reason": "missing_capsule_data",
                        "security_event_id": security_event_id,
                        "timestamp": time.time(),
                    }
                )
            )
            raise MissingFieldError("'capsule' is required in intent_capsule")

        expected_signature = hmac.new(
            self.secret_key.encode(),
            json.dumps(capsule_data, sort_keys=True).encode(),
            hashlib.sha256,
        ).hexdigest()

        if capsule.get("signature") != expected_signature:
            trip_id = capsule_data.get("trip_id", "UNKNOWN")
            logger.warning(
                json.dumps(
                    {
                        "action": "intent_gate_validation",
                        "status": "failed",
                        "security_event_id": security_event_id,
                        "reason": "signature_mismatch",
                        "trip_id": trip_id,
                        "severity": "critical",
                        "timestamp": time.time(),
                    }
                )
            )
            raise TamperingError(
                f"Intent Capsule TAMPERING DETECTED. Signature mismatch."
            )

        # Check 2: Verify expiration (still within time window)
        current_time = time.time()
        expires_at = capsule_data.get("expires_at")

        if expires_at is None:
            logger.error(
                json.dumps(
                    {
                        "action": "intent_gate_validation",
                        "status": "failed",
                        "reason": "missing_expiry",
                        "security_event_id": security_event_id,
                        "timestamp": time.time(),
                    }
                )
            )
            raise MissingFieldError("'expires_at' is required in capsule data")

        if current_time > expires_at:
            trip_id = capsule_data.get("trip_id", "UNKNOWN")
            logger.warning(
                json.dumps(
                    {
                        "action": "intent_gate_validation",
                        "status": "failed",
                        "security_event_id": security_event_id,
                        "reason": "capsule_expired",
                        "trip_id": trip_id,
                        "valid_until": expires_at,
                        "current_time": current_time,
                        "severity": "medium",
                        "timestamp": time.time(),
                    }
                )
            )
            raise ExpirationError(
                f"Intent Capsule EXPIRED. "
                f"Valid until: {expires_at}, Current: {current_time}"
            )

        # Check 3: Verify constraints (if implemented)
        constraints = capsule_data.get("constraints", {})
        max_time = constraints.get("max_compute_time_seconds")
        trip_id = capsule_data.get("trip_id", "UNKNOWN")

        if max_time:
            # Constraint validation framework (can be extended)
            logger.debug(
                json.dumps(
                    {
                        "action": "intent_gate_validation",
                        "status": "constraint_check",
                        "trip_id": trip_id,
                        "constraint": "max_compute_time",
                        "value": max_time,
                        "timestamp": time.time(),
                    }
                )
            )

        # GATE PASSED: Agent is allowed to execute
        logger.info(
            json.dumps(
                {
                    "action": "intent_gate_validation",
                    "status": "passed",
                    "security_event_id": security_event_id,
                    "trip_id": trip_id,
                    "timestamp": time.time(),
                }
            )
        )
        return func(self, state)

    return wrapper
