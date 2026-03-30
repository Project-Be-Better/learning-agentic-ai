# ReAct Agent - Code Organization & Flow Guide

## File Structure & Sections

```
react_agent_organized.py
├── SECTION 1: Configuration
│   └─ LLM setup (model, API key)
│
├── SECTION 2: Tool Definitions
│   └─ estimate_trip_cost() function
│   └─ AVAILABLE_TOOLS dictionary
│
├── SECTION 3: Agent Class
│   └─ ReActAgent class
│   └─ Maintains conversation history
│
├── SECTION 4: Action Parsing
│   └─ parse_action_from_response() — Extract tool calls from LLM output
│   └─ execute_tool() — Run the tool and return result
│
├── SECTION 5: ReAct Loop
│   └─ run_agent_loop() — Main agent loop
│
└── SECTION 6: Usage Examples
    └─ Example 1: Simple query
    └─ Example 2: Complex query (comparison)
```

---

## How Data Flows Through the System

```
User Question
    ↓
run_agent_loop(question)
    ↓
1. Create ReActAgent with system_prompt
    ↓
2. Call agent(next_prompt)  ← TURN BEGINS
    ↓
3. Agent.__call__() adds message to history
    ↓
4. Agent._call_llm() sends full history to OpenAI
    ↓
5. LLM returns response
    (Could be: Thought... Action: tool_name: params OR just Answer)
    ↓
6. parse_action_from_response() extracts tool info
    ↓
7. If action found:
    │  └─ execute_tool(tool_name, params)
    │     └─ Run the function, get result
    │     └─ Return observation
    │
    └─ Observation fed back as next_prompt
       ↓
       LOOP BACK TO STEP 2  ← NEXT TURN
    
    If NO action found:
    │  └─ Agent returned Answer
    │  └─ STOP

```

---

## Key Concepts Mapped to Code

### 1. TOOL DEFINITION
**What it is:** A function the agent can call
**Where in code:** `estimate_trip_cost()` in SECTION 2
**Why:** Agent doesn't know costs; it asks the tool

```python
def estimate_trip_cost(days: int, travelers: int, comfort: str) -> str:
    # Calculate cost based on parameters
    return f"total_estimate: {total}"
```

---

### 2. AGENT CLASS
**What it is:** Maintains conversation history between turns
**Where in code:** `ReActAgent` class in SECTION 3
**Why:** LLM needs to see the entire conversation to make decisions

```python
class ReActAgent:
    def __init__(self, system_prompt):
        self.messages = []  # ← Grows with each turn
        self.messages.append({"role": "system", "content": system_prompt})
    
    def __call__(self, user_message):
        self.messages.append({"role": "user", "content": user_message})
        response = self._call_llm()  # ← LLM sees all messages
        self.messages.append({"role": "assistant", "content": response})
        return response
```

**Message flow:**
```
Turn 1:
  messages = [
    {"role": "system", "content": "You run in a loop..."},
    {"role": "user", "content": "Original question"}
  ]
  → LLM sees: system prompt + original question
  → Returns: "I need to estimate costs. Action: ..."

Turn 2:
  messages = [
    {"role": "system", "content": "You run in a loop..."},
    {"role": "user", "content": "Original question"},
    {"role": "assistant", "content": "I need to estimate. Action: ..."},
    {"role": "user", "content": "Observation: cost is X"}
  ]
  → LLM sees: EVERYTHING from turn 1 + new observation
  → Returns: "Now let me estimate another trip. Action: ..."
```

---

### 3. ACTION PARSING
**What it is:** Extracts tool calls from LLM's natural language
**Where in code:** `parse_action_from_response()` in SECTION 4
**Why:** LLM outputs text like "Action: estimate_trip_cost: 2, 2, mid"
        We need to extract the tool name and parameters

```python
def parse_action_from_response(response_text: str):
    # Looks for lines matching: "Action: <tool_name>: <params>"
    # Returns: (action_name, action_input) or (None, None)
```

**Example:**
```
LLM Response:
"I need to calculate. 
 Action: estimate_trip_cost: 2, 2, mid"

parse_action_from_response() returns:
("estimate_trip_cost", "2, 2, mid")
```

---

### 4. TOOL EXECUTION
**What it is:** Runs the extracted tool with parsed parameters
**Where in code:** `execute_tool()` in SECTION 4
**Why:** Takes raw parameters ("2, 2, mid") and calls the actual function

```python
def execute_tool(tool_name: str, tool_input: str) -> str:
    # 1. Check tool exists
    # 2. Parse parameters (regex)
    # 3. Call function with parsed parameters
    # 4. Return result as string for LLM
```

**Example:**
```
Input: tool_name="estimate_trip_cost", tool_input="2, 2, mid"

Parsing: "2, 2, mid" → days=2, travelers=2, comfort="mid"

Execution: estimate_trip_cost(2, 2, "mid")

Return: "total_estimate: 5000"
```

---

### 5. REACT LOOP
**What it is:** The main orchestration loop
**Where in code:** `run_agent_loop()` in SECTION 5
**Why:** Coordinates agent calls, action parsing, tool execution, and looping

```python
def run_agent_loop(question: str, max_turns: int = 10):
    agent = ReActAgent(system_prompt)
    next_prompt = question
    
    while turn < max_turns:
        # Step 1: Call agent
        response = agent(next_prompt)
        
        # Step 2: Parse action
        action_name, action_input = parse_action_from_response(response)
        
        # Step 3: If action found, execute and feed back
        if action_name:
            observation = execute_tool(action_name, action_input)
            next_prompt = f"Observation: {observation}"
            # ← Loop back to Step 1 with new prompt
        else:
            # ← No action = Answer found, stop
            return
```

---

## Example Walkthrough

**Question:** "Which costs less: Tokyo 2-day mid or Malaysia 3-day premium?"

```
TURN 1:
  next_prompt = "Which costs less: Tokyo 2-day mid or Malaysia 3-day premium?"
  
  agent(next_prompt) calls LLM with:
    system: "You run in a loop of Thought, Action, Observation..."
    user: "Which costs less: ..."
  
  LLM returns:
    "I need to estimate both trips.
     Action: estimate_trip_cost: 2, 2, mid"
  
  parse_action_from_response() → ("estimate_trip_cost", "2, 2, mid")
  
  execute_tool() → estimate_trip_cost(2, 2, "mid") → "total_estimate: 5000"
  
  next_prompt = "Observation: total_estimate: 5000"

TURN 2:
  agent(next_prompt) calls LLM with:
    system: "You run in a loop..."
    user: "Which costs less: ..."
    assistant: "I need to estimate. Action: estimate_trip_cost: 2, 2, mid"
    user: "Observation: total_estimate: 5000"
  
  LLM sees the previous turn and the observation!
  LLM returns:
    "Tokyo costs 5000. Now let me estimate Malaysia.
     Action: estimate_trip_cost: 3, 2, premium"
  
  parse_action_from_response() → ("estimate_trip_cost", "3, 2, premium")
  
  execute_tool() → estimate_trip_cost(3, 2, "premium") → "total_estimate: 10000"
  
  next_prompt = "Observation: total_estimate: 10000"

TURN 3:
  agent(next_prompt) calls LLM with:
    [All previous messages from Turn 1 + Turn 2]
    user: "Observation: total_estimate: 10000"
  
  LLM sees: both previous estimates + current observation
  LLM returns:
    "Based on my calculations:
     - Tokyo (2 days, 2 adults, mid): 5000 SGD
     - Malaysia (3 days, 2 adults, premium): 10000 SGD
     Answer: Tokyo is cheaper by 5000 SGD."
  
  parse_action_from_response() → (None, None)  [No action found]
  
  LOOP STOPS. Agent has the answer.
```

---

## Reading Guide

**If you want to understand:**

1. **How tools work** → Read SECTION 2 (Tool Definitions)
2. **How agent maintains context** → Read SECTION 3 (Agent Class)
3. **How to extract tool calls** → Read SECTION 4 (Action Parsing)
4. **How it all loops together** → Read SECTION 5 (ReAct Loop)
5. **What the agent should do** → Read System Prompt in run_agent_loop()

---

## Running It

```bash
pip install openai python-dotenv

# .env.local
OPENAI_API_KEY=sk-...

python react_agent_organized.py
```

**Output shows:**
- Each turn clearly labeled
- What the agent says
- Which tool it wants to call
- What the tool returned
- The loop continuing until Answer

---

## Key Takeaway

The ReAct pattern is:

```
1. Agent THINKS (via LLM)
2. Agent ACTS (decides to call a tool)
3. Agent OBSERVES (gets tool result)
4. Repeat until Answer

All of this is orchestrated by:
- System prompt (tells agent how to behave)
- Message history (gives agent context)
- Action parsing (extracts decisions)
- Tool execution (runs the decisions)
- Main loop (coordinates everything)
```

Each section in the organized code handles one of these pieces.