"""
Test ScoringAgent: Tool Calling + Scoring (Demo Version)

This test demonstrates:
1. Agent ABC pattern with concrete ScoringAgent
2. LLM calling tools to get trip data
3. LLM reasoning about the data
4. Agent synthesizing valid scoring JSON

DEMO APPROACH:
- Tools return HARDCODED JSON (no Redis needed)
- LLM still reasons about results
- Tests the ARCHITECTURE, not the data infrastructure
- Perfect for team demo

When ready to add real data:
- Replace hardcoded JSON in tools.py with redis_client.get()
- Everything else stays the same
"""

import json
import re

from adapters import AnthropicModel, load_llm

from agents.scoring.agent import ScoringAgent

# ==============================================================================
# TEST
# ==============================================================================


def test_scoring_agent_demo():
    """
    Test ScoringAgent end-to-end with HARDCODED DATA.

    Steps:
    1. Load LLM from adapter
    2. Create ScoringAgent (no Redis needed — tools are hardcoded)
    3. Call agent.invoke_with_trip(trip_id)
    4. Verify result is valid scoring JSON
    """
    print("\n" + "=" * 70)
    print("TEST: ScoringAgent with Tool Calling (Demo Version)")
    print("=" * 70 + "\n")

    # STEP 1: Load LLM
    print("[Step 1] Loading LLM from adapter...")
    try:
        config = load_llm(AnthropicModel.CLAUDE_35_HAIKU_20241022)
        print(f"✓ Loaded: {config.provider} ({config.model})\n")
    except EnvironmentError as e:
        print(f"✗ Error: {e}")
        print("\nSetup required:")
        print("  .env.local with:")
        print("    LLM_PROVIDER=anthropic")
        print("    ANTHROPIC_API_KEY=sk-ant-...\n")
        return False

    llm = config.adapter.get_chat_model()

    # STEP 2: Create ScoringAgent
    # Note: NO Redis injected — tools are hardcoded
    print("[Step 2] Creating ScoringAgent...")
    agent = ScoringAgent(llm=llm, redis_client=None)
    print(f"✓ Agent created: {agent}\n")

    # STEP 3: Run agent
    print("[Step 3] Running agent (tools return hardcoded data)...\n")
    print("-" * 70)
    try:
        trip_id = "TRIP-T12345-2026-03-07-08:00"
        result = agent.invoke_with_trip(trip_id)
        print("-" * 70 + "\n")

        # Extract result
        messages = result.get("messages", [])
        if not messages:
            print("✗ No messages in result")
            return False

        # Get final message
        final_msg = messages[-1]
        if hasattr(final_msg, "content"):
            response_text = final_msg.content
        else:
            response_text = str(final_msg)

        print("[Step 4] Parsing scoring result...\n")

        # Try to extract JSON from response
        try:
            # Look for JSON in the response
            json_match = re.search(
                r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", response_text, re.DOTALL
            )
            if json_match:
                scoring_json = json.loads(json_match.group())
            else:
                # Try direct parse
                scoring_json = json.loads(response_text)
        except json.JSONDecodeError:
            print("✗ Could not parse scoring JSON from response:")
            print(f"Response:\n{response_text}\n")
            return False

        # Validate result
        print("SCORING RESULT")
        print("-" * 70)
        print(f"Trip ID:           {scoring_json.get('trip_id', 'N/A')}")
        print(f"Behaviour Score:   {scoring_json.get('behaviour_score', 'N/A')} / 100")
        print(f"Score Label:       {scoring_json.get('score_label', 'N/A')}")
        print(f"Coaching Required: {scoring_json.get('coaching_required', 'N/A')}")

        if "score_breakdown" in scoring_json:
            bd = scoring_json["score_breakdown"]
            print("\nScore Breakdown:")
            print(f"  Jerk:    {bd.get('jerk_component', 'N/A')} / 40")
            print(f"  Speed:   {bd.get('speed_component', 'N/A')} / 25")
            print(f"  Lateral: {bd.get('lateral_component', 'N/A')} / 20")
            print(f"  Engine:  {bd.get('engine_component', 'N/A')} / 15")

        # Assertions
        print("\n" + "-" * 70)
        print("VALIDATION")
        print("-" * 70)

        score = scoring_json.get("behaviour_score")
        label = scoring_json.get("score_label")
        coaching = scoring_json.get("coaching_required")

        checks = []

        # Check 1: Score is 0-100
        if isinstance(score, (int, float)) and 0 <= score <= 100:
            print("✓ behaviour_score is 0-100")
            checks.append(True)
        else:
            print(f"✗ behaviour_score is invalid: {score}")
            checks.append(False)

        # Check 2: Label is valid
        valid_labels = ["Excellent", "Good", "Average", "Below Average", "Poor"]
        if label in valid_labels:
            print(f"✓ score_label is valid: {label}")
            checks.append(True)
        else:
            print(f"✗ score_label is invalid: {label}")
            checks.append(False)

        # Check 3: Coaching is boolean
        if isinstance(coaching, bool):
            print(f"✓ coaching_required is boolean: {coaching}")
            checks.append(True)
        else:
            print(f"✗ coaching_required is not boolean: {coaching}")
            checks.append(False)

        # Check 4: Score matches label
        if (
            (label == "Excellent" and score >= 85)
            or (label == "Good" and 70 <= score < 85)
            or (label == "Average" and 55 <= score < 70)
            or (label == "Below Average" and 40 <= score < 55)
            or (label == "Poor" and score < 40)
        ):
            print("✓ score matches label")
            checks.append(True)
        else:
            print(f"✗ score ({score}) does not match label ({label})")
            checks.append(False)

        if all(checks):
            print("\n✓ TEST PASSED\n")
            return True
        else:
            print(f"\n✗ TEST FAILED ({sum(checks)}/{len(checks)} checks passed)\n")
            return False

    except Exception as e:
        print(f"✗ Agent invocation failed: {e}\n")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_scoring_agent_demo()
    exit(0 if success else 1)
