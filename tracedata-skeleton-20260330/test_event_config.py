from models.event_config import EVENT_MATRIX, Action, Priority

# Test 1: Load harsh_brake event
event = EVENT_MATRIX["harsh_brake"]
assert event.action == Action.COACHING
assert event.priority == Priority.HIGH

# Test 2: Check security
assert event.scope.requires_hmac == True
assert "scoring" in [a.value for a in event.scope.allowed_agents]

# Test 3: Check execution workflow
assert event.execution_workflow.execution_policy.name == "SEQUENTIAL"

print("✅ All EventConfig tests passed!")
