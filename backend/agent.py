import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition

from crud_tools import all_tools

load_dotenv()

# Ensure Gemini API key is provided
if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("GEMINI_API_KEY environment variable is not set.")

# Initialize the Gemini model with tool binding
llm = ChatGoogleGenerativeAI(
    model="gemini-flash-latest",
    temperature=0
)
llm_with_tools = llm.bind_tools(all_tools)

# System prompt that strictly enforces pre-fetching before mutation
SYSTEM_PROMPT = """You are an accurate and helpful Database Administrator AI assistant for an employee directory.
Your role is to manage records in the 'employees' table (fields: id, name, department, position, email, phone) using your provided tools.

STRICT OPERATIONAL GUIDELINES:
1. ALWAYS call `get_records` to look up existing records BEFORE attempting an `update_record` or `delete_record` operation, unless the user has explicitly provided the confirmed numeric ID in this turn. This guarantees you are acting on the correct record.
2. For `create_record`, ensure all required fields (name, department, position, email) are supplied. If any required information is missing, ask the user for clarification before calling the tool.
3. Keep responses clean, concise, and report the outcome directly to the user.
"""

def agent_node(state: MessagesState):
    """Executes the LLM node with system instructions prepended to the message history."""
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

tool_node = ToolNode(all_tools)

# Construct LangGraph StateGraph
builder = StateGraph(MessagesState)

builder.add_node("agent", agent_node)
builder.add_node("tools", tool_node)

builder.add_edge(START, "agent")
# Route to tool execution if the model invoked a tool; otherwise route to END
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")

# Compile into an executable graph
agent_executor = builder.compile()


def process_query(user_message: str) -> str:
    """Invokes the LangGraph state machine with the user's natural language message."""
    input_state = {"messages": [HumanMessage(content=user_message)]}
    final_state = agent_executor.invoke(input_state)
    last_msg = final_state["messages"][-1]
    content = last_msg.content
    if isinstance(content, list):
        text_parts = [
            part["text"] for part in content if isinstance(part, dict) and "text" in part
        ] or [str(p) for p in content]
        return "\n".join(text_parts)
    return str(content)
