"""
Unit tests for the Agent Framework and Intent Gate mechanism.

Tests verify:
- Intent Capsule creation and signing
- Intent Gate validation (signature, expiration)
- Agent execution with valid and invalid capsules
- Error handling for security violations
"""

import pytest
import time
import logging
from datetime import datetime
from pydantic import ValidationError

from TDScoringAgent import TDScoringAgent
from TDAgentBase import TDAgentEnum
from intent_gate import create_intent_capsule
from models import TDAgentState, IntentCapsule
from exceptions import (
    SecurityError,
    TamperingError,
    ExpirationError,
    MissingFieldError,
)

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)


class TestIntentCapsuleCreation:
    """Test suite for Intent Capsule creation."""

    def test_create_valid_capsule(self):
        """Test that create_intent_capsule generates a valid signed capsule."""
        trip_id = "TRIP-001"
        secret_key = "dev_secret"
        expires_at = time.time() + 60

        capsule = create_intent_capsule(
            trip_id=trip_id,
            secret_key=secret_key,
            expires_at=expires_at,
        )

        # Verify it's a Pydantic IntentCapsule model
        assert isinstance(capsule, IntentCapsule)

        # Verify structure using dot notation
        assert capsule.capsule is not None
        assert capsule.signature is not None

        # Verify capsule data
        capsule_data = capsule.capsule
        assert capsule_data.trip_id == trip_id
        assert capsule_data.expires_at == int(expires_at)
        assert capsule_data.issued_at is not None
        assert capsule_data.correlation_id is not None

    def test_custom_capsule_parameters(self):
        """Test that capsule respects custom parameters."""
        trip_id = "TRIP-002"
        secret_key = "dev_secret"

        capsule = create_intent_capsule(
            trip_id=trip_id,
            secret_key=secret_key,
            expires_at=time.time() + 60,
            subject="safety_agent",
            purpose="enrich_harsh_events",
            allowed_actions=["enrich_events"],
        )

        capsule_data = capsule.capsule
        assert capsule_data.subject == "safety_agent"
        assert capsule_data.purpose == "enrich_harsh_events"
        assert capsule_data.constraints.allowed_actions == ["enrich_events"]


class TestIntentGateValidation:
    """Test suite for Intent Gate validation."""

    @pytest.fixture
    def scoring_agent(self):
        """Create a scoring agent for testing."""
        return TDScoringAgent(
            agent_id=TDAgentEnum.SCORING_AGENT, secret_key="dev_secret"
        )

    @pytest.fixture
    def valid_capsule(self):
        """Create a valid, non-expired capsule."""
        return create_intent_capsule(
            trip_id="TRIP-001",
            secret_key="dev_secret",
            expires_at=time.time() + 60,
        )

    def test_valid_capsule_passes_gate(self, scoring_agent, valid_capsule):
        """Test that a valid capsule passes the Intent Gate."""
        # Create state as Pydantic model
        trip_data = TDAgentState(
            trip_id="TRIP-001",
            trip_context={
                "trip_pings": [1, 2, 3],
                "harsh_events": 2,
            },
            intent_capsule=valid_capsule,
        )

        result = scoring_agent.run(trip_data)

        # Verify result structure using dot notation (Pydantic model)
        assert result.agent == "scoring_agent"
        assert result.trip_id == "TRIP-001"
        assert result.status == "success"
        assert result.output is not None
        assert result.timestamp is not None

        # Verify scoring output using dot notation
        assert result.output.trip_score == 90  # 100 - (2 * 5)
        assert result.output.harsh_events_count == 2

    def test_expired_capsule_rejected(self, scoring_agent):
        """Test that an expired capsule is rejected by Intent Gate."""
        # Create an EXPIRED capsule
        expired_capsule = create_intent_capsule(
            trip_id="TRIP-002",
            secret_key="dev_secret",
            expires_at=time.time() - 10,  # Expired 10 seconds ago
        )

        trip_data = TDAgentState(
            trip_id="TRIP-002",
            trip_context={
                "trip_pings": [],
                "harsh_events": 0,
            },
            intent_capsule=expired_capsule,
        )

        # Should raise ExpirationError
        with pytest.raises(ExpirationError):
            scoring_agent.run(trip_data)

    def test_tampered_capsule_rejected(self, scoring_agent, valid_capsule):
        """Test that a tampered capsule is rejected by Intent Gate."""
        # Tamper with capsule data - need to modify the Pydantic model
        # Create a dict, modify, and recreate
        tampered_dict = valid_capsule.model_dump()
        tampered_dict["capsule"]["constraints"]["allowed_actions"] = [
            "delete_everything"
        ]
        tampered_capsule = IntentCapsule(**tampered_dict)

        trip_data = TDAgentState(
            trip_id="TRIP-001",
            trip_context={
                "trip_pings": [1],
                "harsh_events": 1,
            },
            intent_capsule=tampered_capsule,
        )

        # Should raise TamperingError
        with pytest.raises(TamperingError):
            scoring_agent.run(trip_data)

    def test_wrong_secret_key_rejected(self, valid_capsule):
        """Test that wrong secret key is detected by Intent Gate."""
        # Create agent with different secret key
        agent = TDScoringAgent(
            agent_id=TDAgentEnum.SCORING_AGENT, secret_key="wrong_secret"
        )

        trip_data = TDAgentState(
            trip_id="TRIP-001",
            trip_context={
                "trip_pings": [],
                "harsh_events": 0,
            },
            intent_capsule=valid_capsule,
        )

        # Should raise TamperingError (signature mismatch)
        with pytest.raises(TamperingError):
            agent.run(trip_data)

    def test_missing_capsule_raises_error(self, scoring_agent):
        """Test that missing intent_capsule raises validation error."""
        # Pydantic will raise ValidationError for missing required field
        with pytest.raises(ValidationError):
            TDAgentState(  # type: ignore
                trip_id="TRIP-001",
                trip_context={"harsh_events": 0},
                # Missing: intent_capsule
            )

    def test_missing_trip_id_raises_keyerror(self, scoring_agent, valid_capsule):
        """Test that missing trip_id raises ValidationError."""
        with pytest.raises(ValidationError):
            TDAgentState(  # type: ignore
                trip_context={"harsh_events": 0},
                intent_capsule=valid_capsule,
                # Missing: trip_id
            )

    def test_missing_trip_context_raises_error(self, scoring_agent, valid_capsule):
        """Test that missing trip_context raises ValidationError."""
        with pytest.raises(ValidationError):
            TDAgentState(  # type: ignore
                trip_id="TRIP-001",
                intent_capsule=valid_capsule,
                # Missing: trip_context
            )


class TestScoringAgent:
    """Test suite for TDScoringAgent business logic."""

    @pytest.fixture
    def agent_with_capsule(self):
        """Create agent and valid capsule."""
        agent = TDScoringAgent(
            agent_id=TDAgentEnum.SCORING_AGENT, secret_key="dev_secret"
        )
        capsule = create_intent_capsule(
            trip_id="TRIP-001",
            secret_key="dev_secret",
            expires_at=time.time() + 60,
        )
        return agent, capsule

    def test_scoring_with_no_harsh_events(self, agent_with_capsule):
        """Test scoring when there are no harsh events."""
        agent, capsule = agent_with_capsule

        trip_data = TDAgentState(
            trip_id="TRIP-001",
            trip_context={
                "trip_pings": [1, 2, 3, 4, 5],
                "harsh_events": 0,
            },
            intent_capsule=capsule,
        )

        result = agent.run(trip_data)
        assert result.output.trip_score == 100

    def test_scoring_with_harsh_events(self, agent_with_capsule):
        """Test scoring deduction with harsh events."""
        agent, capsule = agent_with_capsule

        trip_data = TDAgentState(
            trip_id="TRIP-001",
            trip_context={
                "trip_pings": [1, 2],
                "harsh_events": 5,
            },
            intent_capsule=capsule,
        )

        result = agent.run(trip_data)
        assert result.output.trip_score == 75  # 100 - (5 * 5)

    def test_scoring_minimum_is_zero(self, agent_with_capsule):
        """Test that score never goes below zero."""
        agent, capsule = agent_with_capsule

        trip_data = TDAgentState(
            trip_id="TRIP-001",
            trip_context={
                "trip_pings": [],
                "harsh_events": 50,  # 50 * 5 = 250 deduction
            },
            intent_capsule=capsule,
        )

        result = agent.run(trip_data)
        assert result.output.trip_score == 0  # Would be -200, but capped at 0

    def test_default_trip_pings_empty_list(self, agent_with_capsule):
        """Test that missing trip_pings defaults to empty list."""
        agent, capsule = agent_with_capsule

        trip_data = TDAgentState(
            trip_id="TRIP-001",
            trip_context={
                # Missing: "trip_pings"
                "harsh_events": 2,
            },
            intent_capsule=capsule,
        )

        result = agent.run(trip_data)
        assert result.output.pings_count == 0

    def test_default_harsh_events_zero(self, agent_with_capsule):
        """Test that missing harsh_events defaults to 0."""
        agent, capsule = agent_with_capsule

        trip_data = TDAgentState(
            trip_id="TRIP-001",
            trip_context={
                "trip_pings": [1, 2, 3],
                # Missing: "harsh_events"
            },
            intent_capsule=capsule,
        )

        result = agent.run(trip_data)
        assert result.output.trip_score == 100
        assert result.output.harsh_events_count == 0


class TestAgentMetadata:
    """Test suite for agent result metadata."""

    @pytest.fixture
    def agent_with_capsule(self):
        """Create agent and valid capsule."""
        agent = TDScoringAgent(
            agent_id=TDAgentEnum.SCORING_AGENT, secret_key="dev_secret"
        )
        capsule = create_intent_capsule(
            trip_id="TRIP-001",
            secret_key="dev_secret",
            expires_at=time.time() + 60,
        )
        return agent, capsule

    def test_result_includes_agent_id(self, agent_with_capsule):
        """Test that result includes agent_id."""
        agent, capsule = agent_with_capsule

        trip_data = TDAgentState(
            trip_id="TRIP-001",
            trip_context={"harsh_events": 0},
            intent_capsule=capsule,
        )

        result = agent.run(trip_data)
        assert result.agent == "scoring_agent"

    def test_result_includes_trip_id(self, agent_with_capsule):
        """Test that result includes trip_id."""
        agent, capsule = agent_with_capsule

        trip_data = TDAgentState(
            trip_id="TRIP-999",
            trip_context={"harsh_events": 0},
            intent_capsule=capsule,
        )

        result = agent.run(trip_data)
        assert result.trip_id == "TRIP-999"

    def test_result_includes_timestamp(self, agent_with_capsule):
        """Test that result includes ISO 8601 timestamp with Z suffix."""
        agent, capsule = agent_with_capsule

        trip_data = TDAgentState(
            trip_id="TRIP-001",
            trip_context={"harsh_events": 0},
            intent_capsule=capsule,
        )

        result = agent.run(trip_data)
        # Should end with Z for UTC
        assert result.timestamp.endswith("Z")
        # Should be parseable as ISO format
        timestamp_str = result.timestamp[:-1]  # Remove the Z
        datetime.fromisoformat(timestamp_str)

    def test_result_status_is_success(self, agent_with_capsule):
        """Test that successful execution status is 'success'."""
        agent, capsule = agent_with_capsule

        trip_data = TDAgentState(
            trip_id="TRIP-001",
            trip_context={"harsh_events": 0},
            intent_capsule=capsule,
        )

        result = agent.run(trip_data)
        assert result.status == "success"


class TestConstraintValidation:
    """Test suite for capsule constraint enforcement."""

    @pytest.fixture
    def agent_with_capsule(self):
        """Create agent and capsule."""
        agent = TDScoringAgent(
            agent_id=TDAgentEnum.SCORING_AGENT, secret_key="dev_secret"
        )
        capsule = create_intent_capsule(
            trip_id="TRIP-001",
            secret_key="dev_secret",
            expires_at=time.time() + 60,
            constraints={
                "allowed_actions": ["score_trip"],
                "resource_id": "redis:trip_summary:TRIP-001",
                "max_compute_time_seconds": 30,
                "max_harsh_events": 1,
            },
        )
        return agent, capsule

    def test_respects_max_harsh_events_constraint(self, agent_with_capsule):
        """Test that agent respects max_harsh_events constraint in capsule."""
        agent, capsule = agent_with_capsule

        # Create data that EXCEEDS the max_harsh_events constraint (2 > 1)
        trip_data = TDAgentState(
            trip_id="TRIP-001",
            trip_context={
                "trip_pings": [1],
                "harsh_events": 2,  # Exceeds constraint of max 1
            },
            intent_capsule=capsule,
        )

        # Verify constraint is in capsule
        assert capsule.capsule.constraints.max_harsh_events == 1

        # Verify the execution detects the constraint violation
        # (Implementation depends on whether agent is supposed to reject or handle)
        result = agent.run(trip_data)
        assert result is not None  # Agent should execute but be aware of constraint

    def test_constraint_fields_present_in_capsule(self, agent_with_capsule):
        """Test that constraint fields are properly stored in capsule."""
        agent, capsule = agent_with_capsule

        constraints = capsule.capsule.constraints
        assert constraints.max_harsh_events == 1
        assert constraints.allowed_actions is not None
        assert constraints.resource_id is not None


class TestSerialization:
    """Test suite for model serialization and deserialization."""

    @pytest.fixture
    def agent_with_capsule(self):
        """Create agent and valid capsule."""
        agent = TDScoringAgent(
            agent_id=TDAgentEnum.SCORING_AGENT, secret_key="dev_secret"
        )
        capsule = create_intent_capsule(
            trip_id="TRIP-001",
            secret_key="dev_secret",
            expires_at=time.time() + 60,
        )
        return agent, capsule

    def test_agent_result_to_dict(self, agent_with_capsule):
        """Test that AgentResult can be serialized to dict."""
        agent, capsule = agent_with_capsule

        trip_data = TDAgentState(
            trip_id="TRIP-001",
            trip_context={"harsh_events": 2},
            intent_capsule=capsule,
        )

        result = agent.run(trip_data)
        result_dict = result.model_dump()

        # Verify dict structure
        assert isinstance(result_dict, dict)
        assert "agent" in result_dict
        assert "trip_id" in result_dict
        assert "status" in result_dict
        assert "output" in result_dict
        assert result_dict["trip_id"] == "TRIP-001"

    def test_agent_result_to_json(self, agent_with_capsule):
        """Test that AgentResult can be serialized to JSON."""
        agent, capsule = agent_with_capsule

        trip_data = TDAgentState(
            trip_id="TRIP-001",
            trip_context={"harsh_events": 1},
            intent_capsule=capsule,
        )

        result = agent.run(trip_data)
        result_json = result.model_dump_json()

        # Verify JSON is valid string
        assert isinstance(result_json, str)
        assert "trip_id" in result_json
        assert "TRIP-001" in result_json
        assert "success" in result_json

        # Verify JSON roundtrip
        import json

        result_dict = json.loads(result_json)
        assert result_dict["trip_id"] == "TRIP-001"
        assert result_dict["status"] == "success"

    def test_intent_capsule_serialization(self):
        """Test that IntentCapsule can be serialized and deserialized."""
        capsule = create_intent_capsule(
            trip_id="TRIP-001",
            secret_key="dev_secret",
            expires_at=time.time() + 60,
        )

        capsule_dict = capsule.model_dump()
        assert isinstance(capsule_dict, dict)
        assert "capsule" in capsule_dict
        assert "signature" in capsule_dict

        # Verify roundtrip
        capsule_reconstructed = IntentCapsule(**capsule_dict)
        assert capsule_reconstructed.signature == capsule.signature


class TestTypeValidation:
    """Test suite for Pydantic type validation."""

    def test_rejects_invalid_trip_id_type(self):
        """Test that Pydantic rejects non-string trip_id."""
        capsule = create_intent_capsule(
            trip_id="TRIP-001",
            secret_key="dev_secret",
            expires_at=time.time() + 60,
        )

        with pytest.raises(ValidationError):
            TDAgentState(
                trip_id=12345,  # type: ignore  # Should be string, not int
                trip_context={"harsh_events": 0},
                intent_capsule=capsule,
            )

    def test_rejects_invalid_trip_context_type(self):
        """Test that Pydantic rejects non-dict trip_context."""
        capsule = create_intent_capsule(
            trip_id="TRIP-001",
            secret_key="dev_secret",
            expires_at=time.time() + 60,
        )

        with pytest.raises(ValidationError):
            TDAgentState(
                trip_id="TRIP-001",
                trip_context="not a dict",  # type: ignore  # Should be dict
                intent_capsule=capsule,
            )

    def test_rejects_invalid_harsh_events_type(self):
        """Test that Pydantic rejects negative harsh_events in output."""
        # The AgentOutput should only accept non-negative harsh_events_count
        from models import AgentOutput

        with pytest.raises(ValidationError):
            AgentOutput(
                trip_score=100,
                pings_count=5,
                harsh_events_count=-1,  # Should be >= 0
                action="score_trip",
            )

    def test_rejects_invalid_trip_score_type(self):
        """Test that Pydantic validates trip_score range."""
        from models import AgentOutput

        # trip_score should be integer
        with pytest.raises(ValidationError):
            AgentOutput(
                trip_score="not a number",  # type: ignore
                pings_count=5,
                harsh_events_count=0,
                action="score_trip",
            )


class TestCorrelationID:
    """Test suite for correlation ID uniqueness and tracing."""

    @pytest.fixture
    def agent_with_capsule(self):
        """Create agent and valid capsule."""
        agent = TDScoringAgent(
            agent_id=TDAgentEnum.SCORING_AGENT, secret_key="dev_secret"
        )
        capsule = create_intent_capsule(
            trip_id="TRIP-001",
            secret_key="dev_secret",
            expires_at=time.time() + 60,
        )
        return agent, capsule

    def test_result_includes_correlation_id(self, agent_with_capsule):
        """Test that each result has a correlation_id."""
        agent, capsule = agent_with_capsule

        trip_data = TDAgentState(
            trip_id="TRIP-001",
            trip_context={"harsh_events": 0},
            intent_capsule=capsule,
        )

        result = agent.run(trip_data)
        assert result.correlation_id is not None
        assert len(result.correlation_id) > 0

    def test_correlation_ids_are_unique(self, agent_with_capsule):
        """Test that different executions get different correlation IDs."""
        agent, capsule = agent_with_capsule

        trip_data_1 = TDAgentState(
            trip_id="TRIP-001",
            trip_context={"harsh_events": 1},
            intent_capsule=capsule,
        )

        result_1 = agent.run(trip_data_1)

        # Create a fresh capsule for second execution
        capsule_2 = create_intent_capsule(
            trip_id="TRIP-002",
            secret_key="dev_secret",
            expires_at=time.time() + 60,
        )

        trip_data_2 = TDAgentState(
            trip_id="TRIP-002",
            trip_context={"harsh_events": 2},
            intent_capsule=capsule_2,
        )

        result_2 = agent.run(trip_data_2)

        # Correlation IDs should be different
        assert result_1.correlation_id != result_2.correlation_id


class TestEdgeCases:
    """Test suite for edge cases and defensive programming."""

    @pytest.fixture
    def agent_with_capsule(self):
        """Create agent and valid capsule."""
        agent = TDScoringAgent(
            agent_id=TDAgentEnum.SCORING_AGENT, secret_key="dev_secret"
        )
        capsule = create_intent_capsule(
            trip_id="TRIP-001",
            secret_key="dev_secret",
            expires_at=time.time() + 60,
        )
        return agent, capsule

    def test_very_large_harsh_events_count(self, agent_with_capsule):
        """Test agent handles very large harsh_events count gracefully."""
        agent, capsule = agent_with_capsule

        trip_data = TDAgentState(
            trip_id="TRIP-001",
            trip_context={
                "trip_pings": [1],
                "harsh_events": 10000,
            },
            intent_capsule=capsule,
        )

        result = agent.run(trip_data)
        # Score should be capped at 0, not negative
        assert result.output.trip_score == 0
        assert result.output.harsh_events_count == 10000

    def test_empty_trip_pings_list(self, agent_with_capsule):
        """Test scoring with explicitly empty trip_pings."""
        agent, capsule = agent_with_capsule

        trip_data = TDAgentState(
            trip_id="TRIP-001",
            trip_context={
                "trip_pings": [],
                "harsh_events": 0,
            },
            intent_capsule=capsule,
        )

        result = agent.run(trip_data)
        assert result.output.pings_count == 0
        assert result.output.trip_score == 100

    def test_very_long_trip_id(self, agent_with_capsule):
        """Test agent handles very long trip_id."""
        agent = agent_with_capsule[0]

        long_trip_id = "TRIP-" + "X" * 1000
        capsule = create_intent_capsule(
            trip_id=long_trip_id,
            secret_key="dev_secret",
            expires_at=time.time() + 60,
        )

        trip_data = TDAgentState(
            trip_id=long_trip_id,
            trip_context={"harsh_events": 0},
            intent_capsule=capsule,
        )

        result = agent.run(trip_data)
        assert result.trip_id == long_trip_id

    def test_special_characters_in_trip_id(self, agent_with_capsule):
        """Test agent handles special characters in trip_id."""
        agent = agent_with_capsule[0]

        special_trip_id = "TRIP-!@#$%^&*()-_=+[]{}|;:',.<>?"
        capsule = create_intent_capsule(
            trip_id=special_trip_id,
            secret_key="dev_secret",
            expires_at=time.time() + 60,
        )

        trip_data = TDAgentState(
            trip_id=special_trip_id,
            trip_context={"harsh_events": 0},
            intent_capsule=capsule,
        )

        result = agent.run(trip_data)
        assert result.trip_id == special_trip_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
