# Professor's Hello World - Understanding the Flow

## What It Does

Takes a user question → calls OpenAI LLM → formats output → returns result.

Two-node pipeline: `llm_step` → `format_output` → END

---

## The Moving Parts (Same as Always)

### STATE
```python
class LLMProcessingState(TypedDict):
    user_input: str              # What the user asks
    llm_response: str            # LLM's answer
    processing_steps: list[str]  # Track what we did
```

### NODES (Two of them)

**Node 1: `llm_step`**
- Takes state
- Calls OpenAI via LangChain ChatOpenAI
- Returns state with llm_response filled in
- Logs "Called LLM" to processing_steps

**Node 2: `format_output`**
- Takes state (with llm_response already filled)
- Formats the output as a readable string
- Returns state with formatted response
- Logs "Formatted output" to processing_steps

### EDGES (Fixed routing)

```
Entry → llm_step → format_output → END
```

Fixed edges (not conditional):
- Entry goes to "llm"
- "llm" always goes to "format"
- "format" always goes to END

### GRAPH

Wire nodes + edges, compile, invoke.

---

## Run It

### Setup
```bash
pip install langgraph langchain langchain-openai python-dotenv

# .env.local
OPENAI_API_KEY=sk-...
```

### In Jupyter Notebook
Copy each cell (sections between `# %%`) into separate cells and run.

### Or as Python Script
```bash
python professors_hello_world.py
```

---

## What You'll See

```
✅ API key loaded successfully
What is LangGraph and why is it useful?

LLM replied: [Claude's response here]

Steps taken: ['Called LLM', 'Formatted output']

[Graph visualization as PNG]
```

---

## Key Differences from My Version

| My Version | Professor's |
|-----------|-----------|
| Conditional edge (can loop) | Fixed edges (linear flow) |
| Direct Anthropic client | LangChain ChatOpenAI wrapper |
| Single node | Two nodes (llm + format) |
| Raw dicts for messages | LangChain HumanMessage objects |
| No visualization | Graph visualization included |

---

## Next Steps After Running

1. **Run it** — Feel the flow
2. **Refactor it** — Change something (e.g., add a node, change the prompt)
3. **Run refactored version** — In another workbook
4. **Move to next example** — From professor's course

---

## Questions to Ask Yourself While Running

- Where does the state flow?
- How do nodes modify it?
- Why two nodes instead of one?
- What would happen if you added a third node?
- Can you make an edge conditional?

Answer these, then refactor.