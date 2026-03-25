"""Backward compatible API endpoints."""
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any
from src.agent.graph import get_agent
from src.agent.state import AgentState
from langchain_core.messages import HumanMessage
from src.utils.logger import logger
import uuid

router = APIRouter(tags=["backward-compatible"])


@router.post("/api/v1/analyze")
async def analyze_query(request_body: Dict[str, Any] = Body(...)):
    """Simple analysis endpoint (backward compatible).
    
    Simple interface for quick analysis without thread management.
    """
    query = request_body.get("query", "")
    
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    try:
        agent = get_agent()
        
        # Build simple state
        state: AgentState = {
            "messages": [HumanMessage(content=query)],
            "conversation_history": [],
            "user_context": {},
            "session_id": str(uuid.uuid4()),
            "user_preferences": {},
            "current_task": None,
            "task_history": [],
            "is_simple_question": None,
            "tool_results": {},
            "performance_metrics": {},
            "errors": [],
            "out_of_scope": None,
            "scope_reason": None,
            "scope_redirect_message": None,
            "last_provider_used": None,
            "query_complexity": None,
            "crypto_symbol": None,
        }
        
        # Run agent
        result = await agent.ainvoke(state)
        
        # Extract response
        if result.get("messages"):
            for msg in reversed(result["messages"]):
                if hasattr(msg, 'content'):
                    return {"response": msg.content}
        
        return {"response": "No response generated"}
        
    except Exception as e:
        logger.error(f"Analyze error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/indicators")
async def get_indicators():
    """Get indicator information + top 5 tokens."""
    query = "What technical indicators do you support? Show top 5 tokens by volume."
    
    try:
        agent = get_agent()
        
        state: AgentState = {
            "messages": [HumanMessage(content=query)],
            "conversation_history": [],
            "user_context": {},
            "session_id": str(uuid.uuid4()),
            "user_preferences": {},
            "current_task": None,
            "task_history": [],
            "is_simple_question": None,
            "tool_results": {},
            "performance_metrics": {},
            "errors": [],
            "out_of_scope": None,
            "scope_reason": None,
            "scope_redirect_message": None,
            "last_provider_used": None,
            "query_complexity": None,
            "crypto_symbol": None,
        }
        
        result = await agent.ainvoke(state)
        
        if result.get("messages"):
            for msg in reversed(result["messages"]):
                if hasattr(msg, 'content'):
                    return {"response": msg.content}
        
        return {"response": "No response"}
        
    except Exception as e:
        logger.error(f"Indicators error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/patterns")
async def get_patterns():
    """Get pattern information + top 5 tokens."""
    query = "What chart patterns do you recognize? Show top 5 tokens by volume."
    
    try:
        agent = get_agent()
        
        state: AgentState = {
            "messages": [HumanMessage(content=query)],
            "conversation_history": [],
            "user_context": {},
            "session_id": str(uuid.uuid4()),
            "user_preferences": {},
            "current_task": None,
            "task_history": [],
            "is_simple_question": None,
            "tool_results": {},
            "performance_metrics": {},
            "errors": [],
            "out_of_scope": None,
            "scope_reason": None,
            "scope_redirect_message": None,
            "last_provider_used": None,
            "query_complexity": None,
            "crypto_symbol": None,
        }
        
        result = await agent.ainvoke(state)
        
        if result.get("messages"):
            for msg in reversed(result["messages"]):
                if hasattr(msg, 'content'):
                    return {"response": msg.content}
        
        return {"response": "No response"}
        
    except Exception as e:
        logger.error(f"Patterns error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/support-resistance")
async def get_support_resistance():
    """Get support/resistance info + top 5 tokens."""
    query = "Explain support and resistance levels. Show top 5 tokens by volume."
    
    try:
        agent = get_agent()
        
        state: AgentState = {
            "messages": [HumanMessage(content=query)],
            "conversation_history": [],
            "user_context": {},
            "session_id": str(uuid.uuid4()),
            "user_preferences": {},
            "current_task": None,
            "task_history": [],
            "is_simple_question": None,
            "tool_results": {},
            "performance_metrics": {},
            "errors": [],
            "out_of_scope": None,
            "scope_reason": None,
            "scope_redirect_message": None,
            "last_provider_used": None,
            "query_complexity": None,
            "crypto_symbol": None,
        }
        
        result = await agent.ainvoke(state)
        
        if result.get("messages"):
            for msg in reversed(result["messages"]):
                if hasattr(msg, 'content'):
                    return {"response": msg.content}
        
        return {"response": "No response"}
        
    except Exception as e:
        logger.error(f"Support/Resistance error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/divergences")
async def get_divergences():
    """Get divergence info + top 5 tokens."""
    query = "Explain divergences in technical analysis. Show top 5 tokens by volume."
    
    try:
        agent = get_agent()
        
        state: AgentState = {
            "messages": [HumanMessage(content=query)],
            "conversation_history": [],
            "user_context": {},
            "session_id": str(uuid.uuid4()),
            "user_preferences": {},
            "current_task": None,
            "task_history": [],
            "is_simple_question": None,
            "tool_results": {},
            "performance_metrics": {},
            "errors": [],
            "out_of_scope": None,
            "scope_reason": None,
            "scope_redirect_message": None,
            "last_provider_used": None,
            "query_complexity": None,
            "crypto_symbol": None,
        }
        
        result = await agent.ainvoke(state)
        
        if result.get("messages"):
            for msg in reversed(result["messages"]):
                if hasattr(msg, 'content'):
                    return {"response": msg.content}
        
        return {"response": "No response"}
        
    except Exception as e:
        logger.error(f"Divergences error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
