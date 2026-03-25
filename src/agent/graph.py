"""Main agent graph entry point."""
from langgraph.graph import StateGraph, END
from src.agent.state import AgentState
from src.agent.nodes import router_node, quick_response_node
from src.utils.logger import logger


def create_agent():
    """Create and compile the agent graph."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("quick_response", quick_response_node)
    
    # Set entry point
    workflow.set_entry_point("router")
    
    # Add routing logic
    def route_after_router(state: AgentState) -> str:
        is_simple = state.get("is_simple_question", False)
        return "quick_response" if is_simple else "quick_response"
    
    workflow.add_conditional_edges(
        "router",
        route_after_router,
        {"quick_response": "quick_response"}
    )
    
    workflow.add_edge("quick_response", END)
    
    # Compile
    agent = workflow.compile()
    logger.info("Agent graph compiled successfully")
    
    return agent


# Global agent instance
_agent = None


def get_agent():
    """Get or create agent instance."""
    global _agent
    if _agent is None:
        _agent = create_agent()
    return _agent

