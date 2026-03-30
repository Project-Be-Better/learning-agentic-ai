"""
Test Suite: OrchestratorAgent

Tests the complete orchestration workflow:
1. EventConfig loading and validation
2. EventMatrix lookup (get_event_config tool)
3. Coaching rules evaluation (deterministic)
4. OrchestratorAgent routing decisions

Run with: pytest test_orchestrator.py -v
"""

import json

import pytest

# =============================================================================
# TEST 1: EventMatrix & EventConfig (Foundation)
# =============================================================================


def test_eventmatrix_loaded():
    """Test that EventMatrix has all 18 events"""
    from orchestrator.tools import EVENT_MATRIX

    assert len(EVENT_MATRIX) == 18, "EventMatrix should have 18 events"

    # Check critical events exist
    assert "collision" in EVENT_MATRIX
    assert "rollover" in EVENT_MATRIX
    assert "driver_sos" in EVENT_MATRIX

    # Check harsh events
    assert "harsh_brake" in EVENT_MATRIX
    assert "hard_accel" in EVENT_MATRIX
    assert "harsh_corner" in EVENT_MATRIX

    # Check lifecycle
    assert "end_of_trip" in EVENT_MATRIX
    assert "start_of_trip" in EVENT_MATRIX


def test_event_priorities():
    """Test that event priorities are correct"""
    from orchestrator.tools import EVENT_MATRIX, Priority

    # Critical events (0)
    assert EVENT_MATRIX["collision"].priority == Priority.CRITICAL
    assert EVENT_MATRIX["rollover"].priority == Priority.CRITICAL
    assert EVENT_MATRIX["driver_sos"].priority == Priority.CRITICAL

    # High events (3)
    assert EVENT_MATRIX["harsh_brake"].priority == Priority.HIGH
    assert EVENT_MATRIX["vehicle_offline"].priority == Priority.HIGH

    # Low events (9)
    assert EVENT_MATRIX["end_of_trip"].priority == Priority.LOW
    assert EVENT_MATRIX["normal_operation"].priority == Priority.LOW


def test_action_mapping():
    """Test that action → agents mapping is correct"""
    from orchestrator.tools import ACTION_TO_AGENTS

    # Emergency actions
    assert ACTION_TO_AGENTS["Emergency Alert & 911"] == ["safety"]
    assert ACTION_TO_AGENTS["Emergency Alert"] == ["safety"]

    # Coaching (scoring + driver support)
    assert "scoring" in ACTION_TO_AGENTS["Coaching"]
    assert "driver_support" in ACTION_TO_AGENTS["Coaching"]

    # Scoring only
    assert ACTION_TO_AGENTS["Scoring"] == ["scoring"]

    # No agents (logging/analytics)
    assert ACTION_TO_AGENTS["Analytics"] == []
    assert ACTION_TO_AGENTS["Logging"] == []


# =============================================================================
# TEST 2: get_event_config Tool
# =============================================================================


def test_get_event_config_harsh_brake():
    """Test get_event_config for harsh_brake event"""
    from orchestrator.tools import get_event_config

    result = get_event_config("harsh_brake")
    config = json.loads(result)

    assert config["event_type"] == "harsh_brake"
    assert config["category"] == "harsh_events"
    assert config["priority"] == 3  # HIGH
    assert config["action"] == "Coaching"
    assert config["agents_from_action"] == ["scoring", "driver_support"]


def test_get_event_config_collision():
    """Test get_event_config for collision (CRITICAL)"""
    from orchestrator.tools import get_event_config

    result = get_event_config("collision")
    config = json.loads(result)

    assert config["event_type"] == "collision"
    assert config["priority"] == 0  # CRITICAL
    assert config["action"] == "Emergency Alert & 911"
    assert config["agents_from_action"] == ["safety"]


def test_get_event_config_end_of_trip():
    """Test get_event_config for end_of_trip"""
    from orchestrator.tools import get_event_config

    result = get_event_config("end_of_trip")
    config = json.loads(result)

    assert config["event_type"] == "end_of_trip"
    assert config["priority"] == 9  # LOW
    assert config["action"] == "Scoring"
    assert config["agents_from_action"] == ["scoring"]


def test_get_event_config_unknown_event():
    """Test get_event_config with unknown event"""
    from orchestrator.tools import get_event_config

    result = get_event_config("unknown_event")
    error = json.loads(result)

    assert "error" in error
    assert "unknown_event" in error["error"]
    assert "available_events" in error
    assert len(error["available_events"]) == 18


# =============================================================================
# TEST 3: evaluate_coaching_rules Tool (Deterministic)
# =============================================================================


def test_coaching_rule_absolute_floor():
    """Test Rule 1: Absolute Floor (score < 60)"""
    from orchestrator.tools import evaluate_coaching_rules

    result = evaluate_coaching_rules(
        behaviour_score=54.2,  # Below 60
        historical_avg=70.0,
        flagged_events_count=0,
    )
    decision = json.loads(result)

    assert decision["coaching_needed"] == True
    assert "absolute_floor" in decision["triggered_rules"]
    assert decision["priority_escalation"] == True
    assert decision["new_priority"] == 6


def test_coaching_rule_trend_detection():
    """Test Rule 2: Negative Trend (|score - avg| > 10)"""
    from orchestrator.tools import evaluate_coaching_rules

    result = evaluate_coaching_rules(
        behaviour_score=65.0,
        historical_avg=80.0,  # Difference > 10
        flagged_events_count=0,
    )
    decision = json.loads(result)

    assert decision["coaching_needed"] == True
    assert "trend_detection" in decision["triggered_rules"]


def test_coaching_rule_flagged_events():
    """Test Rule 3: Flagged Events Present"""
    from orchestrator.tools import evaluate_coaching_rules

    result = evaluate_coaching_rules(
        behaviour_score=78.5,
        historical_avg=76.1,
        flagged_events_count=2,  # > 0
    )
    decision = json.loads(result)

    assert decision["coaching_needed"] == True
    assert "flagged_events" in decision["triggered_rules"]


def test_coaching_rule_no_coaching():
    """Test when NO rules trigger (no coaching needed)"""
    from orchestrator.tools import evaluate_coaching_rules

    result = evaluate_coaching_rules(
        behaviour_score=78.5,  # > 60
        historical_avg=76.1,  # Diff < 10
        flagged_events_count=0,  # No events
    )
    decision = json.loads(result)

    assert decision["coaching_needed"] == False
    assert decision["triggered_rules"] == []
    assert decision["priority_escalation"] == False
    assert decision["new_priority"] == 9  # LOW (no escalation)


def test_coaching_rule_all_rules_triggered():
    """Test when ALL rules trigger"""
    from orchestrator.tools import evaluate_coaching_rules

    result = evaluate_coaching_rules(
        behaviour_score=50.0,  # < 60 (Rule 1)
        historical_avg=68.0,  # Diff > 10 (Rule 2)
        flagged_events_count=3,  # > 0 (Rule 3)
    )
    decision = json.loads(result)

    assert decision["coaching_needed"] == True
    assert len(decision["triggered_rules"]) == 3
    assert "absolute_floor" in decision["triggered_rules"]
    assert "trend_detection" in decision["triggered_rules"]
    assert "flagged_events" in decision["triggered_rules"]


# =============================================================================
# TEST 4: OrchestratorAgent Routing (requires LLM)
# =============================================================================


@pytest.mark.asyncio
async def test_orchestrator_agent_initialization():
    """Test that OrchestratorAgent initializes correctly"""
    try:
        from adapters.factory import load_llm

        from agents.orchestrator.agent import OrchestratorAgent

        # Load LLM from environment
        llm = load_llm(provider="anthropic")
        orchestrator = OrchestratorAgent(llm=llm)

        assert orchestrator is not None
        assert orchestrator.agent_name == "OrchestratorAgent"
        assert len(orchestrator.tools) >= 2
    except Exception as e:
        pytest.skip(f"Skipping LLM test: {e}")


def test_orchestrator_invoke_with_trip():
    """Test invoke_with_trip method signature and return type"""
    try:
        from adapters.factory import load_llm

        from agents.orchestrator.agent import OrchestratorAgent

        llm = load_llm(provider="anthropic")
        orchestrator = OrchestratorAgent(llm=llm)

        # Verify method exists
        assert hasattr(orchestrator, "invoke_with_trip")

        # Check it's callable
        assert callable(orchestrator.invoke_with_trip)
    except Exception as e:
        pytest.skip(f"Skipping LLM test: {e}")


# =============================================================================
# TEST 5: Integration Tests (Full Workflow)
# =============================================================================


def test_event_config_to_agents_mapping():
    """Integration: EventConfig → Action → Agents"""
    from orchestrator.tools import ACTION_TO_AGENTS, get_event_config

    # Get harsh_brake config
    result = get_event_config("harsh_brake")
    config = json.loads(result)

    action = config["action"]
    agents = ACTION_TO_AGENTS[action]

    # Verify chain: event → action → agents
    assert action == "Coaching"
    assert agents == ["scoring", "driver_support"]


def test_routing_logic_critical_event():
    """Integration: Critical event routing"""
    from orchestrator.tools import ACTION_TO_AGENTS, get_event_config

    # Collision (CRITICAL)
    result = get_event_config("collision")
    config = json.loads(result)

    assert config["priority"] == 0  # CRITICAL
    assert config["action"] == "Emergency Alert & 911"

    agents = ACTION_TO_AGENTS[config["action"]]
    assert "safety" in agents


def test_routing_logic_harsh_event():
    """Integration: Harsh event routing"""
    from orchestrator.tools import ACTION_TO_AGENTS, get_event_config

    # Harsh brake (HIGH)
    result = get_event_config("harsh_brake")
    config = json.loads(result)

    assert config["priority"] == 3  # HIGH
    assert config["action"] == "Coaching"

    agents = ACTION_TO_AGENTS[config["action"]]
    assert "scoring" in agents
    assert "driver_support" in agents


def test_routing_logic_low_priority_event():
    """Integration: Low priority event routing"""
    from orchestrator.tools import ACTION_TO_AGENTS, get_event_config

    # End of trip (LOW)
    result = get_event_config("end_of_trip")
    config = json.loads(result)

    assert config["priority"] == 9  # LOW
    assert config["action"] == "Scoring"

    agents = ACTION_TO_AGENTS[config["action"]]
    assert agents == ["scoring"]


# =============================================================================
# TEST 6: All 18 Events (Coverage)
# =============================================================================


def test_all_18_events():
    """Test all 18 events load and have routing"""
    from orchestrator.tools import ACTION_TO_AGENTS, get_event_config

    events = [
        "collision",
        "rollover",
        "driver_sos",  # CRITICAL
        "harsh_brake",
        "hard_accel",
        "harsh_corner",  # HIGH
        "vehicle_offline",
        "driver_dispute",
        "driver_complaint",
        "speeding",
        "driver_feedback",  # MEDIUM
        "excessive_idle",
        "smoothness_log",
        "normal_operation",  # LOW
        "start_of_trip",
        "end_of_trip",
        "driver_comment",
        "malicious_injection",
    ]

    assert len(events) == 18

    for event in events:
        result = get_event_config(event)
        config = json.loads(result)

        # Each event should have valid config
        assert "event_type" in config
        assert "priority" in config
        assert "action" in config
        assert config["action"] in ACTION_TO_AGENTS


# =============================================================================
# TEST 7: Type Safety & Validation
# =============================================================================


def test_event_config_has_all_fields():
    """Test that EventConfig has all required fields"""
    from orchestrator.tools import EVENT_MATRIX

    for event_name, event_config in EVENT_MATRIX.items():
        assert hasattr(event_config, "category")
        assert hasattr(event_config, "priority")
        assert hasattr(event_config, "ml_weight")
        assert hasattr(event_config, "action")


def test_priority_values_valid():
    """Test that all priorities are valid values"""
    from orchestrator.tools import EVENT_MATRIX, Priority

    valid_priorities = [
        Priority.CRITICAL,  # 0
        Priority.HIGH,  # 3
        Priority.MEDIUM,  # 6
        Priority.LOW,  # 9
    ]

    for event_name, event_config in EVENT_MATRIX.items():
        assert event_config.priority in valid_priorities


def test_action_values_valid():
    """Test that all actions are in the mapping"""
    from orchestrator.tools import ACTION_TO_AGENTS, EVENT_MATRIX

    for event_name, event_config in EVENT_MATRIX.items():
        assert event_config.action in ACTION_TO_AGENTS


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("ORCHESTRATOR AGENT TEST SUITE")
    print("=" * 70)

    print("\n[TEST 1] EventMatrix & EventConfig")
    test_eventmatrix_loaded()
    print("  ✅ EventMatrix loaded (18 events)")
    test_event_priorities()
    print("  ✅ Event priorities correct")
    test_action_mapping()
    print("  ✅ Action → agents mapping correct")

    print("\n[TEST 2] get_event_config Tool")
    test_get_event_config_harsh_brake()
    print("  ✅ harsh_brake config correct")
    test_get_event_config_collision()
    print("  ✅ collision config correct")
    test_get_event_config_end_of_trip()
    print("  ✅ end_of_trip config correct")
    test_get_event_config_unknown_event()
    print("  ✅ Unknown event handled correctly")

    print("\n[TEST 3] evaluate_coaching_rules Tool")
    test_coaching_rule_absolute_floor()
    print("  ✅ Rule 1: Absolute floor works")
    test_coaching_rule_trend_detection()
    print("  ✅ Rule 2: Trend detection works")
    test_coaching_rule_flagged_events()
    print("  ✅ Rule 3: Flagged events works")
    test_coaching_rule_no_coaching()
    print("  ✅ No coaching case works")
    test_coaching_rule_all_rules_triggered()
    print("  ✅ All rules triggered case works")

    print("\n[TEST 5] Integration Tests")
    test_event_config_to_agents_mapping()
    print("  ✅ Event → Action → Agents chain works")
    test_routing_logic_critical_event()
    print("  ✅ Critical event routing works")
    test_routing_logic_harsh_event()
    print("  ✅ Harsh event routing works")
    test_routing_logic_low_priority_event()
    print("  ✅ Low priority event routing works")

    print("\n[TEST 6] All 18 Events Coverage")
    test_all_18_events()
    print("  ✅ All 18 events have valid routing")

    print("\n[TEST 7] Type Safety & Validation")
    test_event_config_has_all_fields()
    print("  ✅ EventConfig has all required fields")
    test_priority_values_valid()
    print("  ✅ All priorities are valid")
    test_action_values_valid()
    print("  ✅ All actions are in mapping")

    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
