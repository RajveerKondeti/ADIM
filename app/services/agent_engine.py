# app/services/agent_engine.py
import os
from typing import Annotated, TypedDict, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage 
from langgraph.graph import StateGraph, END
from neo4j import GraphDatabase

# --- STEP 1: DEFINE STATE FIRST ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "The conversation history"]
    next_step: str
    data_found: bool

# --- STEP 2: DEFINE FUNCTIONS ---
def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.1
    )

def call_model(state: AgentState):
    llm = get_llm()
    response = llm.invoke(state['messages'])
    return {"messages": [response]}

def query_database(state: AgentState):
    print("--- SEARCHING KNOWLEDGE GRAPH ---")
    return {"data_found": True}

def update_knowledge_graph(state: AgentState):
    """
    Example: If Gemini detects a 'Risk', we save that relationship in Neo4j.
    """
    uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    driver = GraphDatabase.driver(uri, auth=("neo4j", os.getenv("NEO4J_PASSWORD")))
    
    with driver.session() as session:
        # Simple Cypher query to create a node
        session.run(
            "MERGE (r:Risk {description: $desc}) "
            "MERGE (s:System {name: 'ADIM_CORE'}) "
            "MERGE (s)-[:DETECTED]->(r)",
            desc="Anomaly detected in operational logs"
        )
    driver.close()
    return {"data_found": True}

# --- STEP 3: BUILD GRAPH ---
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tool", query_database)
workflow.set_entry_point("agent")
workflow.add_edge("agent", "tool")
workflow.add_edge("tool", END)

agent_executor = workflow.compile()