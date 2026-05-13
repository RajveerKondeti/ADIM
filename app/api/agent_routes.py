from fastapi import APIRouter, Depends
from app.services.agent_engine import agent_executor
from langchain_core.messages import HumanMessage 

router = APIRouter()

@router.post("/chat")
async def ask_adim(prompt: str):
    inputs = {"messages": [HumanMessage(content=prompt)]}
    config = {"configurable": {"thread_id": "1"}}
    
    # Run the graph!
    result = await agent_executor.ainvoke(inputs, config)
    
    return {"response": result["messages"][-1].content}