"""
agent_engine.py — ADIM's AI brain.

Current state:  Phase 1 (working LangGraph agent with Gemini).
                RAG is stubbed out cleanly — enable it in Phase 2 once
                the embedding pipeline is wired up.

Architecture:
    User prompt → AgentState → [call_model node] → [query_db node] → Response

The graph is intentionally simple right now. As ADIM grows, we add:
    - conditional routing (agent decides which tool to call)
    - parallel nodes (risk agent + opportunity agent simultaneously)
    - human-in-the-loop pause nodes
    - memory retrieval node (long-term context from Qdrant)
"""
import logging
import os
from typing import Annotated, List, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph

from app.core.config import settings

logger = logging.getLogger(__name__)


# ── State ─────────────────────────────────────────────────────────────────────
# This "sticky note" flows through every node in the graph.
# Annotated[List[...], "..."] tells LangGraph to APPEND messages, not replace.

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "conversation history — appended, not replaced"]
    data_found: bool


# ── LLM factory ───────────────────────────────────────────────────────────────

def _get_llm() -> ChatGoogleGenerativeAI:
    """Instantiated fresh per call — avoids stale state across requests."""
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.1,
    )


# ── Nodes ─────────────────────────────────────────────────────────────────────

def call_model(state: AgentState) -> dict:
    """Node 1: Send the conversation to Gemini and get a response."""
    llm = _get_llm()
    response: AIMessage = llm.invoke(state["messages"])
    return {"messages": [response]}


def query_knowledge_graph(state: AgentState) -> dict:
    """
    Node 2: Placeholder for Neo4j knowledge graph lookup.
    Phase 2: extract entities from the LLM response and search Neo4j.
    """
    logger.debug("Knowledge graph query — stub, returning no data.")
    return {"data_found": False}


# ── Graph assembly ────────────────────────────────────────────────────────────

_workflow = StateGraph(AgentState)
_workflow.add_node("agent", call_model)
_workflow.add_node("knowledge_graph", query_knowledge_graph)
_workflow.set_entry_point("agent")
_workflow.add_edge("agent", "knowledge_graph")
_workflow.add_edge("knowledge_graph", END)

agent_executor = _workflow.compile()


# ── Public API ────────────────────────────────────────────────────────────────

def generate_response(prompt: str) -> str:
    """
    Main entry point for the agent.

    Args:
        prompt: The fully constructed prompt (context + user question).

    Returns:
        The agent's text response.
    """
    initial_state: AgentState = {
        "messages": [HumanMessage(content=prompt)],
        "data_found": False,
    }

    try:
        result = agent_executor.invoke(initial_state)
        last_message = result["messages"][-1]
        return last_message.content
    except Exception as e:
        logger.error(f"Agent invocation failed: {e}")
        return f"I encountered an error processing your request. Please try again."


# ── RAG (Phase 2 — disabled until embedding pipeline is wired) ────────────────
# Uncomment and implement after:
#   1. pip install sentence-transformers
#   2. Create the Qdrant collection
#   3. Build the ingestion pipeline

# from qdrant_client import QdrantClient
# from sentence_transformers import SentenceTransformer
#
# _qdrant = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
# _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
#
# def get_rag_context(query: str) -> str:
#     query_vector = _embed_model.encode(query).tolist()
#     results = _qdrant.search(
#         collection_name=settings.QDRANT_COLLECTION,
#         query_vector=query_vector,
#         limit=3,
#     )
#     return "\n\n".join(r.payload["text"] for r in results)