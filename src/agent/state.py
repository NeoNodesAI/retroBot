"""Agent state management for LangGraph."""
from typing import TypedDict, Annotated, Optional, Dict, List
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State structure for retroBot Agent."""
    
    messages: Annotated[List, add_messages]
    conversation_history: List[Dict]
    user_context: Dict
    session_id: str
    user_preferences: Dict
    current_task: Optional[str]
    task_history: List[Dict]
    is_simple_question: Optional[bool]
    tool_results: Dict
    performance_metrics: Dict
    errors: List[Dict]
    out_of_scope: Optional[bool]
    last_provider_used: Optional[str]
    query_complexity: Optional[Dict]
    scope_reason: Optional[str]
    scope_redirect_message: Optional[str]
    retro_command_response: Optional[str]
    crypto_symbol: Optional[str]

