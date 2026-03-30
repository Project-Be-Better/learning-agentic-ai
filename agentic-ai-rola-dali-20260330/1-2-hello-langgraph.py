import operator
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

# Load environment variables
load_dotenv()

# 1. Define the State
# Annotated[list, operator.add] means new lists returned by nodes 
# will be APPENDED to the existing messages list.
class GraphState(TypedDict):
    messages: Annotated[list, operator.add]

# 2. Define the Node
# A simple function that calls OpenAI
def call_model(state: GraphState):
    model = ChatOpenAI(model="gpt-4o")
    response = model.invoke(state["messages"])
    # Return a dict to update the state
    return {"messages": [response]}

# 3. Build the Graph
workflow = StateGraph(GraphState)

# Add our node
workflow.add_node("agent", call_model)

# Set the flow
workflow.set_entry_point("agent")
workflow.add_edge("agent", END)

# 4. Compile it into an executable app
app = workflow.compile()

# 5. Test it
if __name__ == "__main__":
    print("--- Running LangGraph Hello World ---")
    inputs = {"messages": [("user", "Hello! Who are you and what can you do with LangGraph?")]}
    config = {"configurable": {"thread_id": "1"}}
    
    for event in app.stream(inputs, config=config):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)
