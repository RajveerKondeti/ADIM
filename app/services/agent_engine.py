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
    

Phase 2: RAG is live.
  - When use_rag=True, the agent searches Qdrant for relevant context
    before sending the prompt to Gemini.
  - The LLM answers based on YOUR ingested documents, not just its
    training data.
 
Flow:
  prompt → [embed prompt] → [search Qdrant top-3] → [inject context]
         → [Gemini] → [knowledge graph stub] → response 
"""
import logging
from typing import Annotated, List, TypedDict, Optional

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


# ── Nodes ────────────────────────────────────────────────────────────────────

def call_model(state: AgentState) -> dict:
    """Node 1: Send the conversation to Gemini and get a response."""
    llm = _get_llm()
    response: AIMessage = llm.invoke(state["messages"])
    return {"messages": [response]}


def query_knowledge_graph(state: AgentState) -> dict:
    """
    Node 2: Placeholder for Neo4j knowledge graph lookup.
    Phase 2: extract entities from the LLM response and search Neo4j.
    Phase 3: extract entities from response and write to Neo4j
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

# ── RAG context retrieval ─────────────────────────────────────────────────────
 
def _get_rag_context(prompt: str, project_id: Optional[int] = None) -> str:
    """
    Embeds the user's prompt and searches Qdrant for the top-3 most
    semantically similar chunks from ingested documents.
 
    Returns the chunks as a formatted context block, or empty string
    if nothing relevant is found.
    """
    try:
        from app.services.ingestion import embed_query
        from app.services.qdrant_service import search_similar
 
        query_vector = embed_query(prompt)
        chunks = search_similar(
            query_vector=query_vector,
            limit=3,
            project_id=project_id,
        )
 
        if not chunks:
            logger.debug("RAG search returned no results.")
            return ""
 
        context = "\n\n---\n\n".join(chunks)
        logger.debug(f"RAG retrieved {len(chunks)} chunks.")
        return context
 
    except Exception as e:
        # RAG failure should never crash the agent — fall back gracefully
        logger.warning(f"RAG retrieval failed, continuing without context: {e}")
        return ""

# ── Public API ────────────────────────────────────────────────────────────────

def generate_response(prompt: str, use_rag: bool = False, project_id: Optional[int] = None) -> str:
    """
    Main entry point for the agent.

    Args:
        prompt: Fully constructed prompt (system context + user question).
        use_rag: If True, retrieves relevant document chunks from Qdrant
                 and injects them into the prompt before calling the LLM.
        project_id: Scopes RAG search to documents from a specific project.
 
    Returns:
        The agent's text response.
    """
    final_prompt = prompt
 
    if use_rag:
        rag_context = _get_rag_context(prompt, project_id=project_id)
        if rag_context:
            final_prompt = (
                f"{prompt}\n\n"
                f"[RELEVANT KNOWLEDGE BASE CONTEXT]\n"
                f"The following excerpts from ingested documents are relevant "
                f"to the question above. Use them to ground your answer:\n\n"
                f"{rag_context}"
            )
 
    initial_state: AgentState = {
        "messages": [HumanMessage(content=final_prompt)],
        "data_found": False,
    }
 
    try:
        result = agent_executor.invoke(initial_state)
        return result["messages"][-1].content
    except Exception as e:
        logger.error(f"Agent invocation failed: {e}")
        return "I encountered an error processing your request. Please try again."


