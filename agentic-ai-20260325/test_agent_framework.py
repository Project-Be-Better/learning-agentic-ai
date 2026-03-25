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

from TDScoringAgent import TDScoringAgent
from TDAgentBase import TDAgentEnum, TDAgentState
from intent_gate import create_intent_capsule
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

        # Verify structure
        assert "capsule" in capsule
        assert "signature" in capsule

        # Verify capsule data
        capsule_data = capsule["capsule"]
        assert capsule_data["trip_id"] == trip_id
        assert capsule_data["expires_at"] == int(expires_at)
        assert "issued_at" in capsule_data
        assert "correlation_id" in capsule_data

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

        capsule_data = capsule["capsule"]
        assert capsule_data["subject"] == "safety_agent"
        assert capsule_data["purpose"] == "enrich_harsh_events"
        assert capsule_data["constraints"]["allowed_actions"] == ["enrich_events"]


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
        trip_data: TDAgentState = {
            "trip_id": "TRIP-001",
            "trip_context": {
                "trip_pings": [1, 2, 3],
                "harsh_events": 2,
            },
            "intent_capsule": valid_capsule,
        }

        result = scoring_agent.run(trip_data)

        # Verify result structure
        assert result["agent"] == "scoring_agent"
        assert result["trip_id"] == "TRIP-001"
        assert result["status"] == "SUCCESS"
        assert "output" in result
        assert "timestamp" in result

        # Verify scoring output
        assert result["output"]["trip_score"] == 90  # 100 - (2 * 5)
        assert result["output"]["harsh_events_count"] == 2

    def test_expired_capsule_rejected(self, scoring_agent):
        """Test that an expired capsule is rejected by Intent Gate."""
        # Create an EXPIRED capsule
        expired_capsule = create_intent_capsule(
            trip_id="TRIP-002",
            secret_key="dev_secret",
            expires_at=time.time() - 10,  # Expired 10 seconds ago
        )

        trip_data: TDAgentState = {
            "trip_id": "TRIP-002",
            "trip_context": {
                "trip_pings": [],
                "harsh_events": 0,
            },
            "intent_capsule": expired_capsule,
        }

        # Should raise ExpirationError
        with pytest.raises(ExpirationError):
            scoring_agent.run(trip_data)

    def test_tampered_capsule_rejected(self, scoring_agent, valid_capsule):
        """Test that a tampered capsule is rejected by Intent Gate."""
        # Tamper with the capsule data
        valid_capsule["capsule"]["constraints"]["allowed_actions"] = [
            "delete_everything"
        ]

        trip_data: TDAgentState = {
            "trip_id": "TRIP-001",
            "trip_context": {
                "trip_pings": [1],
                "harsh_events": 1,
            },
            "intent_capsule": valid_capsule,
        }

        # Should raise TamperingError
        with pytest.raises(TamperingError):
            scoring_agent.run(trip_data)

    def test_wrong_secret_key_rejected(self, valid_capsule):
        """Test that wrong secret key is detected by Intent Gate."""
        # Create agent with different secret key
        agent = TDScoringAgent(
            agent_id=TDAgentEnum.SCORING_AGENT, secret_key="wrong_secret"
        )

        trip_data: TDAgentState = {
            "trip_id": "TRIP-001",
            "trip_context": {
                "trip_pings": [],
                "harsh_events": 0,
            },
            "intent_capsule": valid_capsule,
        }

        # Should raise TamperingError (signature mismatch)
        with pytest.raises(TamperingError):
            agent.run(trip_data)

    def test_missing_capsule_raises_error(self, scoring_agent):
        """Test that missing intent_capsule raises MissingFieldError."""
        trip_data = {
            "trip_id": "TRIP-001",
            "trip_context": {"harsh_events": 0},
            # Missing: "intent_capsule"
        }

        with pytest.raises(MissingFieldError):
            scoring_agent.run(trip_data)

    def test_missing_trip_id_raises_keyerror(self, scoring_agent, valid_capsule):
        """Test that missing trip_id raises KeyError."""
        trip_data = {
            "trip_context": {"harsh_events": 0},
            "intent_capsule": valid_capsule,
        }

        with pytest.raises(KeyError, match="trip_id"):
            scoring_agent.run(trip_data)

    def test_missing_trip_context_raises_error(self, scoring_agent, valid_capsule):
        """Test that missing trip_context raises KeyError."""
        trip_data = {
            "trip_id": "TRIP-001",
            "intent_capsule": valid_capsule,
        }

        with pytest.raises(KeyError, match="trip_context"):
            scoring_agent.run(trip_data)


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

        trip_data: TDAgentState = {
            "trip_id": "TRIP-001",
            "trip_context": {
                "trip_pings": [1, 2, 3, 4, 5],
                "harsh_events": 0,
            },
            "intent_capsule": capsule,
        }

        result = agent.run(trip_data)
        assert result["output"]["trip_score"] == 100

    def test_scoring_with_harsh_events(self, agent_with_capsule):
        """Test scoring deduction with harsh events."""
        agent, capsule = agent_with_capsule

        trip_data: TDAgentState = {
            "trip_id": "TRIP-001",
            "trip_context": {
                "trip_pings": [1, 2],
                "harsh_events": 5,
            },
            "intent_capsule": capsule,
        }

        result = agent.run(trip_data)
        # 100 - (5 * 5) = 75
        assert result["output"]["trip_score"] == 75

    def test_scoring_minimum_is_zero(self, agent_with_capsule):
        """Test that score doesn't go below zero."""
        agent, capsule = agent_with_capsule

        trip_data: TDAgentState = {
            "trip_id": "TRIP-001",
            "trip_context": {
                "trip_pings": [],
                "harsh_events": 50,  # 50 * 5 = 250 deduction
            },
            "intent_capsule": capsule,
        }

        result = agent.run(trip_data)
        assert result["output"]["trip_score"] == 0

    def test_default_trip_pings_empty_list(self, agent_with_capsule):
        """Test that missing trip_pings defaults to empty list."""
        agent, capsule = agent_with_capsule

        trip_data: TDAgentState = {
            "trip_id": "TRIP-001",
            "trip_context": {
                # Missing: "trip_pings"
                "harsh_events": 2,
            },
            "intent_capsule": capsule,
        }

        result = agent.run(trip_data)
        assert result["output"]["pings_count"] == 0

    def test_default_harsh_events_zero(self, agent_with_capsule):
        """Test that missing harsh_events defaults to 0."""
        agent, capsule = agent_with_capsule

        trip_data: TDAgentState = {
            "trip_id": "TRIP-001",
            "trip_context": {
                "trip_pings": [1, 2, 3],
                # Missing: "harsh_events"
            },
            "intent_capsule": capsule,
        }

        result = agent.run(trip_data)
        assert result["output"]["harsh_events_count"] == 0


class TestAgentMetadata:
    """Test suite for agent output metadata."""

    def test_result_includes_agent_id(self):
        """Test that result includes agent id."""
        agent = TDScoringAgent(
            agent_id=TDAgentEnum.SCORING_AGENT, secret_key="dev_secret"
        )
        capsule = create_intent_capsule(
            trip_id="TRIP-001",
            secret_key="dev_secret",
            expires_at=time.time() + 60,
        )

        trip_data: TDAgentState = {
            "trip_id": "TRIP-001",
            "trip_context": {"harsh_events": 0},
            "intent_capsule": capsule,
        }

        result = agent.run(trip_data)
        assert result["agent"] == "scoring_agent"

    def test_result_includes_trip_id(self):
        """Test that result includes trip id."""
        agent = TDScoringAgent(
            agent_id=TDAgentEnum.SCORING_AGENT, secret_key="dev_secret"
        )
        capsule = create_intent_capsule(
            trip_id="TRIP-999",
            secret_key="dev_secret",
            expires_at=time.time() + 60,
        )

        trip_data: TDAgentState = {
            "trip_id": "TRIP-999",
            "trip_context": {"harsh_events": 0},
            "intent_capsule": capsule,
        }

        result = agent.run(trip_data)
        assert result["trip_id"] == "TRIP-999"

    def test_result_includes_timestamp(self):
        """Test that result includes ISO format timestamp."""
        agent = TDScoringAgent(
            agent_id=TDAgentEnum.SCORING_AGENT, secret_key="dev_secret"
        )
        capsule = create_intent_capsule(
            trip_id="TRIP-001",
            secret_key="dev_secret",
            expires_at=time.time() + 60,
        )

        trip_data: TDAgentState = {
            "trip_id": "TRIP-001",
            "trip_context": {"harsh_events": 0},
            "intent_capsule": capsule,
        }

        result = agent.run(trip_data)
        # Should end with Z for UTC
        assert result["timestamp"].endswith("Z")
        # Should be parseable as ISO format
        timestamp_str = result["timestamp"][:-1]  # Remove the Z
        datetime.fromisoformat(timestamp_str)

    def test_result_status_is_success(self):
        """Test that successful execution status is SUCCESS."""
        agent = TDScoringAgent(
            agent_id=TDAgentEnum.SCORING_AGENT, secret_key="dev_secret"
        )
        capsule = create_intent_capsule(
            trip_id="TRIP-001",
            secret_key="dev_secret",
            expires_at=time.time() + 60,
        )

        trip_data: TDAgentState = {
            "trip_id": "TRIP-001",
            "trip_context": {"harsh_events": 0},
            "intent_capsule": capsule,
        }

        result = agent.run(trip_data)
        assert result["status"] == "SUCCESS"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
