from typing import Dict, Any, Optional
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
from models import (
    TDAgentState,
    AgentResult,
    IntentCapsule,
    CapsuleData,
    CapsuleConstraints,
)

logger = logging.getLogger(__name__)


def create_intent_capsule(
    trip_id: str,
    secret_key: str,
    expires_at: float,
    subject: str = "scoring_agent",
    purpose: str = "evaluate_trip_lifecycle",
    allowed_actions: Optional[list] = None,
    constraints: Optional[Dict[str, Any]] = None,
) -> IntentCapsule:
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
        Signed IntentCapsule (Pydantic model)
    """
    if allowed_actions is None:
        allowed_actions = ["score_trip"]

    # Create constraints as CapsuleConstraints model
    if constraints is None:
        constraint_model = CapsuleConstraints(
            allowed_actions=allowed_actions,
            resource_id=f"redis:trip_summary:{trip_id}",
            max_compute_time_seconds=30,
        )
    else:
        constraint_model = CapsuleConstraints(**constraints)

    # Create capsule data as model
    capsule_data_model = CapsuleData(
        correlation_id=f"trip-req-{trip_id}",
        trip_id=trip_id,
        subject=subject,
        purpose=purpose,
        constraints=constraint_model,
        issued_at=int(time.time()),
        expires_at=int(expires_at),
    )

    # Sign it (HMAC-SHA256) - use JSON serialization for hashing
    capsule_dict = capsule_data_model.model_dump(mode="json")
    signature = hmac.new(
        secret_key.encode(),
        json.dumps(capsule_dict, sort_keys=True).encode(),
        hashlib.sha256,
    ).hexdigest()

    # Return Pydantic model
    return IntentCapsule(
        capsule=capsule_data_model,
        signature=signature,
    )


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
    def wrapper(self, state: TDAgentState) -> AgentResult:
        """
        Internal: Verify capsule before agent runs.

        Args:
            self: The agent instance (has secret_key)
            state: The TDAgentState (Pydantic model)

        Returns:
            AgentResult from the original run() method

        Raises:
            TamperingError: If capsule signature verification fails
            ExpirationError: If capsule has expired
            ConstraintViolationError: If capsule constraints are violated
        """
        security_event_id = str(uuid.uuid4())

        # Access capsule using dot notation
        capsule = state.intent_capsule  # Now a Pydantic IntentCapsule
        capsule_data = capsule.capsule  # CapsuleData model
        trip_id = capsule_data.trip_id

        # INTENT GATE VALIDATION

        # Check 1: Verify signature (detect tampering)
        # Recompute signature using dict serialization
        capsule_dict = capsule_data.model_dump(mode="json")
        expected_signature = hmac.new(
            self.secret_key.encode(),
            json.dumps(capsule_dict, sort_keys=True).encode(),
            hashlib.sha256,
        ).hexdigest()

        if capsule.signature != expected_signature:
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
        expires_at = capsule_data.expires_at

        if current_time > expires_at:
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
        constraints = capsule_data.constraints
        max_time = constraints.max_compute_time_seconds

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
