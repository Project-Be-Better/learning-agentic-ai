# ScoringAgent Demo Version — Hardcoded Tools Approach

## Why Hardcoded? (The Teaching Strategy)

You said: **"For the first pass, hardcode responses. Then progressively switch to real logic."**

This is **perfect** for teaching and team demos. Here's why:

---

## The Problem with Building Everything at Once

If we tried to build everything real from the start:

```
✗ Agent ABC + Tools + Redis + Domain Logic + DB + Async
  = 10+ concepts to understand at once
  = Hard to debug when something breaks
  = Team is confused about what failed
  = Takes weeks before you can demo
```

---

## The Hardcoded Approach (What We're Doing)

```
✓ Agent ABC + Tools (hardcoded) 
  = 2 concepts to understand
  = Clear error handling
  = Can demo in 1 day
  = Team learns the PATTERN first
  = Data/logic swapped in progressively
```

---

## Execution Flow (Demo Version)

```
User: python test_scoring_agent.py
  │
  ├─ Load LLM (Claude or GPT)
  ├─ Create ScoringAgent (extends Agent ABC)
  │
  ├─ Call agent.invoke_with_trip("TRIP-T12345-...")
  │   └─ Builds message: "Score this trip. Use tools."
  │
  ├─ LLM sees message + 4 tools
  │   └─ Thinks: "I should call get_trip_context first"
  │
  ├─ LLM calls: get_trip_context("TRIP-T12345-...")
  │   └─ Tool returns HARDCODED JSON:
  │      {
  │        "trip_id": "TRIP-T12345-...",
  │        "driver_id": "DRV-ANON-7829",
  │        "distance_km": 40.3,
  │        ...
  │      }
  │
  ├─ LLM sees data, decides: "Now I need smoothness logs"
  ├─ LLM calls: get_smoothness_logs("TRIP-T12345-...")
  │   └─ Tool returns HARDCODED 6 windows
  │
  ├─ LLM extracts features from windows
  │
  ├─ LLM calls: get_harsh_events("TRIP-T12345-...")
  │   └─ Tool returns HARDCODED 4 harsh brakes
  │
  ├─ LLM calls: compute_behaviour_score(jerk=0.013, ...)
  │   └─ Tool returns HARDCODED score (74.3, Good)
  │
  ├─ LLM synthesizes final JSON:
  │   {
  │     "trip_id": "TRIP-T12345-...",
  │     "behaviour_score": 74.3,
  │     "score_label": "Good",
  │     "score_breakdown": {...},
  │     "coaching_required": true
  │   }
  │
  └─ Test validates: ✓ All checks pass
```

**Key insight:** The LLM still REASONS about the data. It's not hardcoded reasoning — just hardcoded data.

---

## File Structure (Demo Version)

```
agents/scoring/
├─ tools.py           ← HARDCODED DATA at top
│  ├─ DEMO_TRIP_CONTEXT = {...}
│  ├─ DEMO_SMOOTHNESS_LOGS = [...]
│  ├─ DEMO_HARSH_EVENTS = [...]
│  │
│  └─ Functions (same interface):
│     ├─ get_trip_context() → returns DEMO_TRIP_CONTEXT
│     ├─ get_smoothness_logs() → returns DEMO_SMOOTHNESS_LOGS
│     ├─ get_harsh_events() → returns DEMO_HARSH_EVENTS
│     └─ compute_behaviour_score() → returns hardcoded score
│
├─ agent.py           ← ScoringAgent (no changes)
└─ __init__.py        ← Package init

test_scoring_agent.py ← Test (NO MockRedis needed!)
```

---

## The Transition Plan (How to Add Real Data)

### Phase 1: Hardcoded (TODAY ✓)

```python
# tools.py
@tool
def get_trip_context(trip_id: str, redis_client=None) -> str:
    # DEMO: Return hardcoded
    return json.dumps(DEMO_TRIP_CONTEXT)
```

**Advantage:** Runs immediately, no Redis setup.

---

### Phase 2: Redis Integration (Stage 4)

```python
# tools.py (swap out hardcoded, add redis logic)
@tool
def get_trip_context(trip_id: str, redis_client=None) -> str:
    if redis_client is None:
        return json.dumps(DEMO_TRIP_CONTEXT)  # Fallback for testing
    
    key = f"trip:{trip_id}:context"
    context_raw = redis_client.get(key)
    if not context_raw:
        return json.dumps({"error": f"Trip {trip_id} not found"})
    
    return context_raw  # Real data from Redis
```

**Advantage:** Same tool interface, now reads real data.

---

### Phase 3: Domain Functions (Stage 5)

```python
# tools.py (swap hardcoded score, add domain logic)
@tool
def compute_behaviour_score(jerk_mean_avg, ...) -> str:
    # Previously: return json.dumps({...hardcoded...})
    
    # Now: Call real domain function
    from agents.scoring.domain import _compute_trip_score
    
    features = SmoothnessFeatures(
        jerk_mean_avg=jerk_mean_avg,
        ...
    )
    score, breakdown, label = _compute_trip_score(features)
    
    return json.dumps({
        "behaviour_score": score,
        "score_label": label,
        "breakdown": breakdown
    })
```

**Advantage:** Real business logic, same tool interface.

---

## What NEVER Changes

```python
# These stay the same across all phases

# Agent definition
class ScoringAgent(Agent):
    def __init__(self, llm, redis_client=None, repo=None):
        super().__init__(
            llm=llm,
            agent_name="ScoringAgent",
            tools=SCORING_TOOLS,  # ← Same tools list
            system_prompt="..."   # ← Same prompt
        )

# Test entry point
def test_scoring_agent_demo():
    agent = ScoringAgent(llm=llm, redis_client=None)
    result = agent.invoke_with_trip(trip_id)
    # Same assertions
```

**The architecture is frozen. Only the tool internals change.**

---

## Demo Talking Points (For Your Team)

Show them this execution flow:

> **"See how the Agent ABC pattern works?**
> 
> 1. **Define tools** — Functions the LLM can call
> 2. **Create agent** — Pass tools to parent class
> 3. **LLM reasons** — Decides which tools to call
> 4. **Tools execute** — Return JSON
> 5. **LLM synthesizes** — Combines results into final answer
>
> **The tools return hardcoded data today, but the PATTERN is exactly the same when we add Redis, domain logic, DB writes, etc. The architecture doesn't change — only the tool internals.**
>
> Here's the data flowing through the system..."

---

## Hardcoded Data Reference

### Trip Context (from DEMO_TRIP_CONTEXT)
```json
{
  "trip_id": "TRIP-T12345-2026-03-07-08:00",
  "driver_id": "DRV-ANON-7829",
  "truck_id": "T12345",
  "historical_avg_score": 71.2,
  "peer_group_avg": 68.4,
  "duration_minutes": 62,
  "distance_km": 40.3,
  "window_count": 6
}
```

### Smoothness Windows (from DEMO_SMOOTHNESS_LOGS)
```json
[
  {
    "window_index": 0,
    "trip_meter_km": 5.2,
    "jerk_mean": 0.018,
    "jerk_max": 0.072,
    "speed_mean_kmh": 38.4,
    "speed_std_dev": 14.2,
    "mean_lateral_g": 0.04,
    "max_lateral_g": 0.22,
    "mean_rpm": 1640,
    "idle_seconds": 85
  },
  ...6 windows total...
]
```

### Harsh Events (from DEMO_HARSH_EVENTS)
```json
[
  {
    "event_id": "EV-001",
    "event_type": "harsh_brake",
    "trip_meter_km": 4.1,
    "peak_force_g": -0.52,
    "speed_at_event_kmh": 42.0
  },
  ...4 events total...
]
```

---

## Running the Demo

### Prerequisites
```bash
# Install packages
pip install langchain langchain-anthropic langgraph python-dotenv

# Create .env.local
cat > .env.local << EOF
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-haiku-20241022
EOF
```

### Run It
```bash
python test_scoring_agent.py
```

### Expected Output
```
======================================================================
TEST: ScoringAgent with Tool Calling (Demo Version)
======================================================================

[Step 1] Loading LLM from adapter...
✓ Loaded: anthropic (claude-3-5-haiku-20241022)

[Step 2] Creating ScoringAgent...
✓ Agent created: ScoringAgent(tools=4)

[Step 3] Running agent (tools return hardcoded data)...

[Step 4] Parsing scoring result...

SCORING RESULT
----------------------------------------------------------------------
Trip ID:           TRIP-T12345-2026-03-07-08:00
Behaviour Score:   74.3 / 100
Score Label:       Good
Coaching Required: True

Score Breakdown:
  Jerk:    28.4 / 40
  Speed:   18.2 / 25
  Lateral: 19.1 / 20
  Engine:  8.6 / 15

----------------------------------------------------------------------
VALIDATION
----------------------------------------------------------------------
✓ behaviour_score is 0-100
✓ score_label is valid: Good
✓ coaching_required is boolean: True
✓ score matches label

✓ TEST PASSED
```

---

## Phase Progression Checklist

### ✓ Phase 1: Hardcoded (TODAY)
- [ ] `tools.py` with hardcoded DEMO_* constants
- [ ] `agent.py` extends Agent ABC
- [ ] `test_scoring_agent.py` passes
- [ ] Demo to team: "Here's the architecture"

### Phase 2: Redis (After team agrees on data structure)
- [ ] Add `redis_client` to tool implementations
- [ ] Fallback to hardcoded if redis_client is None
- [ ] New test: `test_scoring_agent_with_redis.py`

### Phase 3: Domain Functions (After Phase 2)
- [ ] Extract `agents/scoring/domain.py`
- [ ] Replace hardcoded score with real computation
- [ ] New test: `test_scoring_domain.py`

### Phase 4: DB & Full Pipeline (After Phase 3)
- [ ] Add `ScoringRepo` class
- [ ] Wire LangGraph nodes
- [ ] Integration test: `test_scoring_pipeline.py`

---

## Key Principle: Progressive Enrichment

```
  Hardcoded Data
  │
  ├─ Team understands pattern ✓
  │
  ├─ + Redis Integration
  │   │
  │   ├─ Real trip data ✓
  │   │
  │   ├─ + Domain Functions
  │   │   │
  │   │   ├─ Real scoring logic ✓
  │   │   │
  │   │   ├─ + Full Pipeline
  │   │   │   │
  │   │   │   └─ Production system ✓
```

Each phase:
- ✓ Works and is testable
- ✓ Teaches one more concept
- ✓ Architecture stays the same
- ✓ Only internals change

---

## Why This Works

1. **Clear separation of concerns** — Agent pattern is taught first, data plumbing later
2. **Runnable from day one** — No waiting for Redis setup
3. **Safe for team to see** — Shows architecture before implementation
4. **Easy to extend** — Tools have same interface across all phases
5. **Testable at each phase** — Each phase has working tests

---

## Files You Have

```
✓ agents/scoring/tools.py        (Hardcoded data at top)
✓ agents/scoring/agent.py        (ScoringAgent extends Agent ABC)
✓ agents/scoring/__init__.py     (Package init)
✓ test_scoring_agent.py          (Integration test, no MockRedis)
✓ SCORING_AGENT_GUIDE.md         (Original guide)
✓ LEARNING_PATH_SUMMARY.md       (5-stage plan)
```

---

## Next Step

**Option A:** Run the demo test now
```bash
python test_scoring_agent.py
```

**Option B:** Show teammates and get feedback first

Either way, the structure is set up for progressive enrichment.

Enjoy! 👍