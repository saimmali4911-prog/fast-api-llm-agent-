import os
import re
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition

from crud_tools import all_tools, get_records, create_record, update_record, delete_record

load_dotenv()

# Ensure Gemini API key is provided
if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("GEMINI_API_KEY environment variable is not set.")

# Use the lightest available Gemini model to minimize quota consumption
llm = ChatGoogleGenerativeAI(
    model="gemini-flash-lite-latest",
    temperature=0
)
llm_with_tools = llm.bind_tools(all_tools)

# Concise system prompt — shorter prompts = fewer tokens = less quota used
SYSTEM_PROMPT = """You are a Database Administrator AI for an employee directory.
Manage records (id, name, department, position, email, phone) using your tools.

RULES:
1. Call get_records FIRST before update_record or delete_record (to verify the ID).
2. For create_record, ask for missing required fields (name, department, position, email).
3. Be brief and direct in your responses.
"""

# ─── Fast-path keyword patterns ──────────────────────────────────────────────
# These handle simple requests WITHOUT calling the LLM, saving quota.

_LIST_PATTERNS = re.compile(
    r"\b(list|show|get|display|fetch|view|all|everyone|employees)\b",
    re.IGNORECASE
)
_SEARCH_PATTERNS = re.compile(
    r"\b(who is|find|search|look up|lookup)\b\s+(.+)",
    re.IGNORECASE
)


def _try_fast_path(message: str):
    """
    Attempt to resolve common read queries directly without calling the LLM.
    Returns a string response if handled, or None if the LLM should handle it.
    """
    msg = message.strip().lower()

    # "list all", "show employees", "who works here", "get all", etc.
    if _LIST_PATTERNS.search(msg) and not any(
        kw in msg for kw in ["add", "create", "update", "delete", "remove", "change"]
    ):
        result = get_records.invoke({})
        if "No matching" in result:
            return "The employee directory is currently empty."
        # Format the raw Supabase string response into a readable message
        return f"Here are all employees in the directory:\n\n{result}"

    # "who is Alice", "find Bob", "search for John"
    m = _SEARCH_PATTERNS.search(msg)
    if m:
        name = m.group(2).strip().rstrip("?")
        result = get_records.invoke({"query": name})
        return result

    return None  # Hand off to LLM


# ─── LangGraph state graph ────────────────────────────────────────────────────

def agent_node(state: MessagesState):
    """Executes the LLM node with system instructions prepended to the message history."""
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

tool_node = ToolNode(all_tools)

builder = StateGraph(MessagesState)
builder.add_node("agent", agent_node)
builder.add_node("tools", tool_node)
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")

agent_executor = builder.compile()


def _extract_text(content) -> str:
    """Normalise message content to a plain string."""
    if isinstance(content, list):
        parts = [p["text"] for p in content if isinstance(p, dict) and "text" in p]
        return "\n".join(parts) if parts else str(content)
    return str(content)


def process_query(user_message: str) -> str:
    """
    Main entry point.
    1. Try the fast-path (zero LLM calls for simple reads).
    2. Fall back to the LangGraph agent for complex / write operations.
    """
    # Fast-path: handle simple read queries without touching the LLM
    fast_response = _try_fast_path(user_message)
    if fast_response is not None:
        return fast_response

    # Full agent path for writes and complex natural language
    input_state = {"messages": [HumanMessage(content=user_message)]}
    final_state = agent_executor.invoke(input_state)
    return _extract_text(final_state["messages"][-1].content)
